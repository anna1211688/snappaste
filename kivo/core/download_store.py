# -*- coding: utf-8 -*-
"""无水印下载数据层: 链接清洗、目录管理、yt-dlp 选项与执行。"""
from __future__ import annotations

import os
import re

from . import network
from .i18n import tr

_URL_RE = re.compile(r"https?://[^\s，。；]+")


def clean_url(text):
    """从分享文案中提取第一个 http(s) 链接，并剥掉句末标点/落单右括号。"""
    m = _URL_RE.search(text or "")
    if not m:
        return (text or "").strip()
    u = m.group(0)
    while u:
        if u[-1] in ".,;:!?":
            u = u[:-1]
            continue
        if u[-1] == ")" and u.count(")") > u.count("("):
            u = u[:-1]
            continue
        break
    return u


def default_dir(config):
    d = config.get("Config", "DownloadDir", fallback="") or ""
    return d or os.path.join(os.path.expanduser("~"), "Downloads")


def build_options(outdir, use_cookies, progress_hook=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 3,
        "max_filesize": 4 * 1024 * 1024 * 1024,  # 单文件 4GiB 上限
        "outtmpl": os.path.join(outdir, "%(title).80s [%(id)s].%(ext)s"),
        "format": "best/bv*+ba/bestvideo+bestaudio",
    }
    if progress_hook is not None:
        opts["progress_hooks"] = [progress_hook]
    if use_cookies:
        opts["cookiesfrombrowser"] = ("chrome",)
    proxy = network.active_proxy_url()
    if proxy:
        opts["proxy"] = proxy
    return opts


class DownloadStore:
    def __init__(self, config):
        self.config = config

    def run(self, url, download, outdir, use_cookies, on_progress=None):
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError(tr("dl.missing_yt")) from exc
        os.makedirs(outdir, exist_ok=True)
        opts = build_options(outdir, use_cookies, on_progress)
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=download)

    @staticmethod
    def friendly_error(msg):
        low = (msg or "").lower()
        if "login" in low or "cookies" in low or "sign in" in low:
            return tr("dl.need_login")
        if "unsupported url" in low:
            return tr("dl.unsupported")
        return ""
