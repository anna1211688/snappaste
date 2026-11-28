# -*- coding: utf-8 -*-
"""更新检查与发布签名: 版本比较、资产选择、镜像改写、RSA PKCS#1 v1.5 纯标准库验签。"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import urllib.request

from . import network
from .paths import VERSION
from .i18n import tr

REPO = "anna1211688/KIVO"
RELEASE_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASE_PAGE = f"https://github.com/{REPO}/releases/latest"

_PUBKEY_N = int(
    "CC69B5629CFC5F361709FC436FA1F74858654111AA31E22CB90A4EE859622B7FE3BADB61DF6387250"
    "EA9367AB7669C397E5D3C94DE64A62B4137BD3BD59A647CD775C17E17A87A4204739274C36C1E2F0943"
    "271EA46813A080EF71EA4814A89671F6A7A181DB0BA9C901A042A277D896E7C059D1AC0CEA55F55B3520"
    "34333EF90BAC6E272923D547CCD53FFA06887136420498D50D9F9315AA981DEFB9FCF9E9245F7BFA53ED"
    "73C4F0854E11EB394E61F5731CFD54D230173C85853D618B71EE2B63D2DF66CDC13A354DDD709CFD7C5F"
    "CA8E448C4C1FFE2615A9E0194733F132F74C332E1462FCC360AF5D8BCA68687147E67EBC5747F09E296A"
    "45FA51DF1935", 16)
_PUBKEY_E = 65537


def ver_tuple(s):
    """版本号 -> 可比较元组; 预发布排在同号正式版之前。"""
    s = str(s or "").strip().lstrip("vV")
    main_part, _, pre = s.partition("-")
    nums = [int(x) for x in re.findall(r"\d+", main_part)]
    nums += [0] * (3 - len(nums))
    if not pre:
        return tuple(nums + [1])
    pre_nums = [int(x) for x in re.findall(r"\d+", pre)]
    return tuple(nums + [0] + pre_nums)


def is_newer(latest: str, current: str) -> bool:
    return ver_tuple(latest) > ver_tuple(current)


def pick_setup_asset(data):
    """优先与 tag 同名的安装包, 否则退回首个 KIVO-Setup-*.exe。"""
    assets = (data or {}).get("assets") or []
    ver = str((data or {}).get("tag_name") or "").strip().lstrip("vV")
    fallback = ("", "")
    for a in assets:
        name = str(a.get("name") or "")
        if name.startswith("KIVO-Setup-") and name.lower().endswith(".exe"):
            if ver and name == f"KIVO-Setup-{ver}.exe":
                return str(a.get("browser_download_url") or ""), name
            if not fallback[1]:
                fallback = (str(a.get("browser_download_url") or ""), name)
    return fallback


def pick_sig_asset(data, setup_name):
    want = (setup_name or "") + ".sig"
    for a in data.get("assets") or []:
        if str(a.get("name") or "") == want:
            return str(a.get("browser_download_url") or "")
    return ""


def verify_update_sig(name, version, sha256_hex, sig_b64):
    """RSA PKCS#1 v1.5 + SHA-256 验签, 签名盖在 "文件名\\n版本\\nSHA256"。"""
    try:
        sig = base64.b64decode(sig_b64 or "")
        n, e = _PUBKEY_N, _PUBKEY_E
        k = (n.bit_length() + 7) // 8
        if len(sig) != k:
            return False
        em = pow(int.from_bytes(sig, "big"), e, n).to_bytes(k, "big")
        prefix = bytes.fromhex("3031300d060960864801650304020105000420")
        t = prefix + hashlib.sha256(
            ("%s\n%s\n%s" % (name, version, sha256_hex)).encode("utf-8")).digest()
        if k < len(t) + 11:
            return False
        expected = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
        return hmac.compare_digest(em, expected)
    except Exception:
        return False


def tag_from_location(location):
    marker = "/releases/tag/"
    s = str(location or "")
    if marker not in s:
        return ""
    return s.split(marker, 1)[1].strip("/").split("?", 1)[0].strip()


class UpdateClient:
    def __init__(self, config):
        self.config = config

    def _mirror_base(self):
        return (self.config.get("Network", "UpdateMirror", fallback="") or "").strip().rstrip("/")

    def mirror_rewrite(self, url):
        base = self._mirror_base()
        if not base or not url:
            return url
        m = re.match(r"https?://(?:api\.)?github\.com(/.*)", url)
        return base + m.group(1) if m else url

    def _probe_latest_tag(self, page_url):
        class _RedirectFound(Exception):
            def __init__(self, location):
                self.location = location

        class _StopRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, rq, fp, code, msg, headers, newurl):
                raise _RedirectFound(newurl)

        req = urllib.request.Request(page_url, headers={"User-Agent": "KIVO/" + VERSION})
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler(network._resolve_proxies()), _StopRedirect)
        try:
            opener.open(req, timeout=12)
        except _RedirectFound as e:
            return tag_from_location(e.location)
        return ""

    def fetch_latest_release(self):
        """返回 (tag, html_url, setup_url, setup_name, sig_url); 全失败抛 RuntimeError。"""
        base = self._mirror_base()
        channels = []
        if base:
            channels.append((base + f"/repos/{REPO}/releases/latest",
                             base + f"/{REPO}/releases/latest", True))
        channels.append((RELEASE_API, RELEASE_PAGE, False))
        for api_url, page_url, is_mirror in channels:
            for attempt_timeout in (10, 12):
                try:
                    req = urllib.request.Request(
                        api_url, headers={"User-Agent": "KIVO/" + VERSION,
                                          "Accept": "application/vnd.github+json"})
                    with network.open_url_loose(req, timeout=attempt_timeout) as r:
                        data = json.loads(r.read().decode("utf-8", "replace"))
                    setup_url, setup_name = pick_setup_asset(data)
                    sig_url = pick_sig_asset(data, setup_name) if setup_name else ""
                    if is_mirror:
                        setup_url = self.mirror_rewrite(setup_url)
                        sig_url = self.mirror_rewrite(sig_url)
                    html_url = str(data.get("html_url") or page_url)
                    return (str(data.get("tag_name") or ""), html_url,
                            setup_url, setup_name, sig_url)
                except Exception:
                    continue
            try:
                tag = self._probe_latest_tag(page_url)
                if tag:
                    return tag, page_url, "", "", ""
            except Exception:
                pass
        raise RuntimeError(tr("upd.unreachable"))
