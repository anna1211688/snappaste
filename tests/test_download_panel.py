# -*- coding: utf-8 -*-
"""无水印下载数据层与面板测试。"""
import sys
import types

import pytest

from kivo.core.download_store import (
    DownloadStore, clean_url, default_dir, build_options,
)
from kivo.ui.theme import Theme
from kivo.ui.panels.download_panel import DownloadPanel, _Worker


# ---------- clean_url ----------
def test_clean_plain():
    assert clean_url("https://youtu.be/abc") == "https://youtu.be/abc"


def test_clean_with_text():
    assert clean_url("看这个视频 https://v.douyin.com/x/ 快来看") == "https://v.douyin.com/x/"


def test_clean_trailing_punct():
    assert clean_url("(https://youtu.be/x).") == "https://youtu.be/x"


def test_clean_no_link():
    assert clean_url("没有链接") == "没有链接"


# ---------- 选项 ----------
def test_default_dir():
    from kivo.core.config import ConfigManager
    d = default_dir(ConfigManager())
    assert d.endswith("Downloads")


def test_build_options():
    opts = build_options("/tmp/x", True)
    assert opts["cookiesfrombrowser"] == ("chrome",)
    assert opts["max_filesize"] == 4 * 1024 ** 3
    assert opts["noplaylist"] is True


def test_friendly_error():
    assert "登录" in DownloadStore.friendly_error("Please login required")
    assert "不支持" in DownloadStore.friendly_error("Unsupported URL")
    assert DownloadStore.friendly_error("别的错误") == ""


# ---------- mock yt_dlp ----------
def _mock_ytdlp(info=None):
    mod = types.ModuleType("yt_dlp")

    class _YDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download):
            return info or {"title": "测试", "extractor_key": "TikTok"}

    mod.YoutubeDL = _YDL
    return mod


def test_run_success(monkeypatch):
    monkeypatch.setitem(sys.modules, "yt_dlp", _mock_ytdlp())
    from kivo.core.config import ConfigManager
    store = DownloadStore(ConfigManager())
    info = store.run("https://x", True, "/tmp/dl-test", False)
    assert info["title"] == "测试"


def test_run_missing_ytdlp(monkeypatch):
    monkeypatch.setitem(sys.modules, "yt_dlp", None)
    from kivo.core.config import ConfigManager
    store = DownloadStore(ConfigManager())
    with pytest.raises(RuntimeError):
        store.run("https://x", True, "/tmp/dl-test", False)


# ---------- 面板 ----------
@pytest.fixture
def dp(qapp):
    from kivo.core.config import ConfigManager
    p = DownloadPanel(Theme(False), DownloadStore(ConfigManager()))
    p.show()
    qapp.processEvents()
    return p


def test_invalid_link(dp):
    dp.url_edit.setText("不是链接")
    dp._start(True)
    assert "链接" in dp.status.text()
    assert dp._thread is None


def test_worker_success(monkeypatch, qapp):
    monkeypatch.setitem(sys.modules, "yt_dlp", _mock_ytdlp())
    from kivo.core.config import ConfigManager
    store = DownloadStore(ConfigManager())
    worker = _Worker(store, "https://x", True, "/tmp/dl-test", False)
    captured = []
    worker.finished.connect(lambda i: captured.append(i))
    worker.run()
    qapp.processEvents()
    assert captured and captured[0]["title"] == "测试"


def test_worker_failure(monkeypatch, qapp):
    from kivo.core.config import ConfigManager
    store = DownloadStore(ConfigManager())
    store.run = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    worker = _Worker(store, "https://x", True, "/tmp/dl-test", False)
    captured = []
    worker.failed.connect(lambda m: captured.append(m))
    worker.run()
    qapp.processEvents()
    assert captured == ["boom"]
