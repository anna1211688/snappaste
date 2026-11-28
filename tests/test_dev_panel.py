# -*- coding: utf-8 -*-
"""开发者工具箱数据层与面板测试。"""
import pytest

from kivo.core import devtools
from kivo.ui.theme import Theme
from kivo.ui.panels.dev_panel import DevPanel


# ---------- 数据层 ----------
def test_ts_roundtrip():
    s = devtools.date_to_ts("2026-11-28 12:00:00")
    assert isinstance(s, int)
    assert devtools.ts_to_date(s) == "2026-11-28 12:00:00"


def test_date_to_ts_bad():
    with pytest.raises(ValueError):
        devtools.date_to_ts("瞎写")


def test_json_pretty_minify():
    raw = '{"a":1,"b":2}'
    pretty = devtools.json_pretty(raw)
    assert "\n" in pretty
    minified = devtools.json_minify(raw)
    assert " " not in minified


def test_json_bad():
    with pytest.raises(Exception):
        devtools.json_pretty("{bad")


def test_regex_find():
    hits = devtools.regex_find(r"\d+", "a1 b22 c333")
    assert hits == ["1", "22", "333"]
    hits_ic = devtools.regex_find("abc", "ABC abc", ignore_case=True)
    assert len(hits_ic) == 2


def test_b64_roundtrip():
    enc = devtools.b64_encode("你好")
    assert devtools.b64_decode(enc) == "你好"


def test_unit_convert():
    # 1 km = 1000 m
    assert devtools.unit_convert(1, "length", "km", "m") == 1000
    # 1 KB = 1024 B
    assert devtools.unit_convert(1, "data", "KB", "B") == 1024


# ---------- 面板 ----------
@pytest.fixture
def dp(qapp):
    p = DevPanel(Theme(False))
    p.show()
    qapp.processEvents()
    return p


def test_five_tabs(dp):
    from PySide6.QtWidgets import QTabWidget
    assert dp.findChild(QTabWidget).count() == 5


def test_safe_error_handler(dp):
    called = []
    def boom():
        raise ValueError("x")
    dp._safe(boom, lambda: called.append("err"))
    assert called == ["err"]


def test_safe_success(dp):
    called = []
    dp._safe(lambda: called.append("ok"), lambda: called.append("err"))
    assert called == ["ok"]
