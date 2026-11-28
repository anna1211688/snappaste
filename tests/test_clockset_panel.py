# -*- coding: utf-8 -*-
"""时钟城市选择数据层与面板测试。"""
import pytest

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.core import clock_store
from kivo.ui.theme import Theme
from kivo.ui.panels.clockset_panel import ClockSetPanel


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


@pytest.fixture
def cfg():
    return ConfigManager()


def test_offset_text():
    assert clock_store.offset_text(8) == "UTC+8"
    assert clock_store.offset_text(0) == "UTC"
    assert clock_store.offset_text(-5) == "UTC-5"


def test_search_no_query():
    rows = clock_store.search_cities("")
    assert len(rows) == len(clock_store.CLOCK_CATALOG)


def test_search_with_query():
    rows = clock_store.search_cities("tokyo")
    assert any(tz == "Asia/Tokyo" for _n, tz, _o in rows)


def test_search_global_zone():
    rows = clock_store.search_cities("Reykjavik")
    assert any(tz == "Atlantic/Reykjavik" for _n, tz, _o in rows)


def test_order_picked():
    picked = clock_store.order_picked(["America/New_York", "Asia/Tokyo"])
    # catalog 顺序：东京在纽约前
    assert picked[0] == "Asia/Tokyo"
    assert picked[-1] == "America/New_York"


def test_order_picked_limit():
    many = [tz for _n, tz, _h in clock_store.CLOCK_CATALOG]
    assert len(clock_store.order_picked(many)) <= clock_store.MAX_CITIES


def test_panel_render(qapp, cfg):
    p = ClockSetPanel(Theme(False), cfg)
    p.show()
    qapp.processEvents()
    assert len(p._checks) == len(clock_store.CLOCK_CATALOG)


def test_panel_toggle(qapp, cfg):
    p = ClockSetPanel(Theme(False), cfg)
    p.show()
    # Africa/Cairo 不在默认列表，用于验证添加
    assert "Africa/Cairo" not in p.selected
    p._toggle("Africa/Cairo", True)
    assert "Africa/Cairo" in p.selected


def test_panel_max_limit(qapp, cfg):
    p = ClockSetPanel(Theme(False), cfg)
    p.selected = set(tz for _n, tz, _h in clock_store.CLOCK_CATALOG[:clock_store.MAX_CITIES])
    p.render()
    # 再加一个应被拒绝
    p._toggle("Atlantic/Reykjavik", True)
    assert "Atlantic/Reykjavik" not in p.selected


def test_panel_confirm_empty(qapp, cfg):
    p = ClockSetPanel(Theme(False), cfg)
    p.selected = set()
    p.confirm()
    # 未写配置
    assert cfg.get("Config", "ClockCities", fallback=None) is None


def test_panel_confirm_saves(qapp, cfg):
    p = ClockSetPanel(Theme(False), cfg)
    p.selected = {"Asia/Tokyo", "Asia/Shanghai"}
    done = []
    p.on_done = lambda x: done.append(x)
    p.confirm()
    saved = cfg.get("Config", "ClockCities")
    assert "Asia/Tokyo" in saved and "Asia/Shanghai" in saved
    assert len(done) == 1
