# -*- coding: utf-8 -*-
"""翻译引擎: 百度/有道/谷歌云 + 免费 (gtx/MyMemory), 多通道竞速、LRU 缓存、熔断、多段并行。

只依赖标准库与 ConfigManager; 调用方在后台线程执行。
"""
from __future__ import annotations

import collections
import hashlib
import html
import json
import random
import threading
import time
import uuid
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import network
from .util import redact_secrets

CACHE_MAX = 256
BUDGET = 7.0
GROUP_CHARS = 450

_BAIDU_LANG = {"zh-CN": "zh", "zh-TW": "cht", "ja": "jp", "ko": "kor",
                "fr": "fra", "es": "spa", "vi": "vie"}
_YOUDAO_LANG = {"zh-CN": "zh-CHS", "zh-TW": "zh-CHT"}


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


class TranslateClient:
    def __init__(self, config, translate=None):
        self.config = config
        self._t = translate or (lambda key, zh: zh)
        self._cache = collections.OrderedDict()
        self._lock = threading.Lock()
        self._dead = {}  # name -> (until, soft_count)

    # ---------- 配置 ----------
    def _g(self, key, d=""):
        return (self.config.get("Translate", key, fallback=d) or d).strip()

    def trans_cfg(self):
        svc = self._g("Service", "free") or "free"
        return {
            "service": svc if svc in ("free", "baidu", "youdao", "google") else "free",
            "baidu_id": self._g("BaiduAppId"), "baidu_key": self._g("BaiduKey"),
            "youdao_id": self._g("YoudaoAppId"), "youdao_secret": self._g("YoudaoSecret"),
            "google_key": self._g("GoogleKey")}

    # ---------- 缓存 ----------
    def _cache_get(self, key):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        return None

    def _cache_put(self, key, val):
        with self._lock:
            self._cache[key] = val
            self._cache.move_to_end(key)
            while len(self._cache) > CACHE_MAX:
                self._cache.popitem(last=False)

    # ---------- 熔断 ----------
    def _alive(self, name):
        until, _ = self._dead.get(name, (0, 0))
        return until < time.time()

    def _mark(self, name, ok, hard=False):
        if ok:
            self._dead[name] = (0, 0)
            return
        if hard:
            self._dead[name] = (time.time() + 8, 0)
            return
        until, cnt = self._dead.get(name, (0, 0))
        cnt += 1
        self._dead[name] = (time.time() + 60, 0) if cnt >= 3 else (0, cnt)

    # ---------- 付费/密钥通道 ----------
    def baidu_translate(self, q, target, appid, key, source=None):
        salt = str(random.randint(10000, 99999))
        sign = hashlib.md5(  # nosec - 百度 API 强制 MD5
            (appid + q + salt + key).encode("utf-8")).hexdigest()
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate?" + urllib.parse.urlencode({
            "q": q,
            "from": _BAIDU_LANG.get(source, source) if source else "auto",
            "to": _BAIDU_LANG.get(target, target),
            "appid": appid, "salt": salt, "sign": sign})
        req = urllib.request.Request(url, headers={"User-Agent": "KIVO"})
        with network.open_url(req, timeout=12) as r:
            d = json.loads(r.read().decode("utf-8"))
        if d.get("error_code"):
            raise RuntimeError(f"百度翻译错误 {d.get('error_code')}: {d.get('error_msg', '')}")
        return "\n".join(seg.get("dst", "") for seg in d.get("trans_result") or [])

    def youdao_translate(self, q, target, appkey, secret, source=None):
        salt = str(uuid.uuid4())
        curtime = str(int(time.time()))
        inp = q if len(q) <= 20 else q[:10] + str(len(q)) + q[-10:]
        sign = hashlib.sha256(
            (appkey + inp + salt + curtime + secret).encode("utf-8")).hexdigest()
        data = urllib.parse.urlencode({
            "q": q,
            "from": _YOUDAO_LANG.get(source, source) if source else "auto",
            "to": _YOUDAO_LANG.get(target, target),
            "appKey": appkey, "salt": salt, "sign": sign,
            "signType": "v3", "curtime": curtime}).encode("utf-8")
        req = urllib.request.Request(
            "https://openapi.youdao.com/api", data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "User-Agent": "KIVO"})
        with network.open_url(req, timeout=12) as r:
            d = json.loads(r.read().decode("utf-8"))
        if str(d.get("errorCode", "0")) != "0":
            raise RuntimeError(f"有道翻译错误码 {d.get('errorCode')}")
        return "\n".join(d.get("translation") or [])

    def google_translate(self, q, target, apikey, source=None):
        url = "https://translation.googleapis.com/language/translate/v2?key=" + \
            urllib.parse.quote(apikey)
        params = {"q": q, "target": target, "format": "text"}
        if source:
            params["source"] = source
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "User-Agent": "KIVO"})
        try:
            with network.open_url(req, timeout=12) as r:
                d = json.loads(r.read().decode("utf-8"))
        except Exception:
            raise RuntimeError(redact_secrets("google translate request failed")) from None
        if d.get("error"):
            raise RuntimeError(f"谷歌翻译错误 {d['error'].get('code')}: "
                               f"{d['error'].get('message', '')}")
        trs = (d.get("data") or {}).get("translations") or []
        return html.unescape(trs[0].get("translatedText", "")) if trs else ""

    # ---------- 免费通道 ----------
    def _via_gtx(self, q, target, source):
        url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(
            {"client": "gtx", "sl": source or "auto", "tl": target, "dt": "t", "q": q})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with network.open_url_loose(req, timeout=5) as r:
            d = json.loads(r.read().decode("utf-8"))
        return "".join(seg[0] for seg in (d[0] or []) if seg and seg[0])

    def _via_mymemory(self, q, target, source, cjk):
        src = source or ("zh-CN" if cjk else "en")
        url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(
            {"q": q, "langpair": f"{src}|{target}"})
        req = urllib.request.Request(url, headers={"User-Agent": "KIVO"})
        with network.open_url_loose(req, timeout=6) as r:
            d = json.loads(r.read().decode("utf-8"))
        return (d.get("responseData") or {}).get("translatedText") or ""

    def _via_api(self, q, target, source, tc):
        if tc["service"] == "baidu" and tc["baidu_id"] and tc["baidu_key"]:
            return self.baidu_translate(q, target, tc["baidu_id"], tc["baidu_key"], source)
        if tc["service"] == "youdao" and tc["youdao_id"] and tc["youdao_secret"]:
            return self.youdao_translate(q, target, tc["youdao_id"], tc["youdao_secret"], source)
        if tc["service"] == "google" and tc["google_key"]:
            return self.google_translate(q, target, tc["google_key"], source)
        return ""

    # ---------- 主入口 ----------
    def translate_to(self, text, target, source=None):
        text = (text or "").strip()
        if not text:
            return ""
        cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
        if target == "zh-CN" and source in (None, "zh-CN") and cjk_count >= 3 \
                and cjk_count * 2 >= len(text.replace(" ", "")):
            return text
        cache_key = (text, target, source)
        hit = self._cache_get(cache_key)
        if hit is not None:
            return hit
        cjk = cjk_count > 0

        groups, cur = [], ""
        for line in text.splitlines():
            if cur and len(cur) + len(line) + 1 > GROUP_CHARS:
                groups.append(cur)
                cur = line
            else:
                cur = (cur + "\n" + line) if cur else line
        if cur:
            groups.append(cur)

        try:
            tc = self.trans_cfg()
        except Exception:
            tc = {}
        api_on = ((tc.get("service") == "baidu" and tc.get("baidu_id") and tc.get("baidu_key"))
                  or (tc.get("service") == "youdao" and tc.get("youdao_id")
                      and tc.get("youdao_secret"))
                  or (tc.get("service") == "google" and tc.get("google_key")))

        channels = [("google", lambda g: self._via_gtx(g, target, source)),
                    ("mymemory", lambda g: self._via_mymemory(g, target, source, cjk))]
        if api_on:
            channels.append(("api", lambda g: self._via_api(g, target, source, tc)))

        def one_group(g):
            use = [(n, f) for n, f in channels if self._alive(n)]
            if not use:
                return ""
            ex = ThreadPoolExecutor(max_workers=len(use))
            futs = {ex.submit(fn, g): name for name, fn in use}
            got = ""
            try:
                for fut in as_completed(futs, timeout=BUDGET):
                    name = futs[fut]
                    try:
                        r = fut.result()
                    except Exception:
                        self._mark(name, False, hard=True)
                        continue
                    if r:
                        got = r
                        self._mark(name, True)
                        break
                    self._mark(name, False)
            except Exception:
                got = ""
            finally:
                for fut, name in futs.items():
                    if not fut.done():
                        self._mark(name, False, hard=True)
                ex.shutdown(wait=False)
            return got

        if len(groups) == 1:
            out = [one_group(groups[0])]
        else:
            with ThreadPoolExecutor(max_workers=min(4, len(groups))) as ex:
                out = list(ex.map(one_group, groups))
        if not out or any(not x for x in out):
            return None
        res = "\n".join(out)
        self._cache_put(cache_key, res)
        return res

    def translate(self, text):
        """英文<->简体中文自动方向。"""
        text = (text or "").strip()
        if not text:
            return ""
        return self.translate_to(text, "en" if has_cjk(text) else "zh-CN")
