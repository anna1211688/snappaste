# -*- coding: utf-8 -*-
"""世界时钟数据层与面板测试。"""
from datetime import datetime

import pytest

from kivo.core.clock_store import ClockStore, make_tz, CLOCK_DEFAULT
from kivo.ui.theme import Theme
from kivo.ui.panels.clock_panel import ClockPanel


@pytest.fixture
def cp(qapp):
    from kivo.core.config import ConfigManager
    p = ClockPanel(Theme(False), ClockStore(ConfigManager()))
    p.show()
    qapp.processEvents()
    return p


def test_make_tz():
    tz = make_tz("Asia/Tokyo", 9)
    assert tz is not None


def test_selected_default():
    from kivo.core.config import ConfigManager
    store = ClockStore(ConfigManager())
    sel = store.selected()
    assert len(sel) == len(CLOCK_DEFAULT)
    assert sel[0][1] == "Asia/Shanghai"


def test_convert():
    from datetime import timezone, timedelta
    local = datetime(2026, 11, 28, 19, 48)
    tz = timezone(timedelta(hours=9))
    out = ClockStore.convert(local, tz)
    assert out.tzinfo is not None


def test_cards_count(cp):
    # 本地 + 11 默认
    assert len(cp._cards) == 12


def test_tick_updates(cp):
    cp.tick()
    for tz, time_lab, date_lab, dot in cp._cards:
        assert ":" in time_lab.text()
        assert date_lab.text()


def test_convert_ui(cp):
    cp.my_time.setText("2026-11-28 19:48")
    cp.do_convert()
    assert "对方当地时间" in cp.result_lab.text()


def test_convert_bad_format(cp):
    cp.my_time.setText("瞎写")
    cp.do_convert()
    assert "格式" in cp.result_lab.text()
