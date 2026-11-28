# -*- coding: utf-8 -*-
"""统一网络层: 代理三档 (system/manual/off)、opener 缓存、同主机跳转防护、回环绕过。"""
from __future__ import annotations

import urllib.request as ur
import urllib.error as ue
import urllib.parse as up

from .i18n import tr

_PROXY_CFG = {"mode": "system", "manual": ""}
_PROXY_CACHE = {"sig": None, "strict": None, "loose": None}
_LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "::1")


def normalize_manual_proxy(raw):
    """手动代理规整: 只填 host:port 补 http://, 仅接受 http/https。"""
    s = (raw or "").strip()
    if not s:
        return ""
    if "://" not in s:
        s = "http://" + s
    p = up.urlsplit(s)
    if p.scheme not in ("http", "https") or not p.hostname or not p.port:
        return ""
    return s


def _resolve_proxies():
    mode = _PROXY_CFG.get("mode", "system")
    if mode == "off":
        return {}
    if mode == "manual":
        m = normalize_manual_proxy(_PROXY_CFG.get("manual", ""))
        return {"http": m, "https": m} if m else {}
    return ur.getproxies()


def _proxy_signature(proxies):
    return tuple(sorted((k, str(v)) for k, v in (proxies or {}).items()))


def _build_net_opener(strict):
    proxies = _resolve_proxies()
    sig = _proxy_signature(proxies)
    key = "strict" if strict else "loose"
    if _PROXY_CACHE.get(key) is not None and _PROXY_CACHE.get("sig") == sig:
        return _PROXY_CACHE[key]

    class _LoopbackProxyHandler(ur.ProxyHandler):
        def proxy_open(self, req, proxy, ptype):
            host = (up.urlsplit(req.full_url).hostname or "").lower()
            if host in _LOOPBACK_HOSTS:
                return None
            return super().proxy_open(req, proxy, ptype)

    handlers = [_LoopbackProxyHandler(proxies)]
    if strict:
        class _SameHostRedirect(ur.HTTPRedirectHandler):
            def redirect_request(self, rq, fp, code, msg, headers, newurl):
                old, new = up.urlsplit(rq.full_url), up.urlsplit(newurl)
                dflt = {"http": 80, "https": 443}
                o = (old.scheme, (old.hostname or "").lower(), old.port or dflt.get(old.scheme))
                n = (new.scheme, (new.hostname or "").lower(), new.port or dflt.get(new.scheme))
                if o != n:
                    raise ue.HTTPError(newurl, code, tr("net.redirect"),
                                       headers, fp)
                return super().redirect_request(rq, fp, code, msg, headers, newurl)
        handlers.append(_SameHostRedirect)

    opener = ur.build_opener(*handlers)
    _PROXY_CACHE[key] = opener
    _PROXY_CACHE["sig"] = sig
    return opener


def open_url(req, timeout=None):
    """带同主机跳转防护 (带凭据请求用)。"""
    return _build_net_opener(True).open(req, timeout=timeout)


def open_url_loose(req, timeout=None):
    """允许跨主机跳转 (天气/汇率/更新/在线翻译)。"""
    return _build_net_opener(False).open(req, timeout=timeout)


def set_proxy_config(mode, manual=""):
    _PROXY_CFG["mode"] = mode if mode in ("system", "manual", "off") else "system"
    _PROXY_CFG["manual"] = (manual or "").strip()


def active_proxy_url():
    """供 yt-dlp proxy 参数; 无代理返回 None。"""
    px = _resolve_proxies()
    return px.get("https") or px.get("http") or None
