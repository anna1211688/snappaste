# -*- coding: utf-8 -*-
"""主窗口与导航单元测试 (offscreen)。"""
import pytest

from kivo.ui.theme import Theme
from kivo.ui.main_window import MainWindow, NAV_DEF


@pytest.fixture
def win(qapp):
    qapp.setStyleSheet(Theme(False).base_qss())
    w = MainWindow(Theme(False))
    return w


class TestNavigation:
    def test_all_nav_items_built(self, win):
        keys = {k for k, *_ in NAV_DEF}
        keys.add("settings")
        assert keys.issubset(set(win._nav_items))

    def test_default_shows_clip(self, win):
        assert win._current == "clip"
        assert win.stack.currentWidget() is win._panes["clip"]
        assert win._nav_items["clip"].isChecked()

    def test_select_switches_pane(self, win):
        win.select("ai")
        assert win._current == "ai"
        assert win.stack.currentWidget() is win._panes["ai"]
        assert win._nav_items["ai"].isChecked()
        assert not win._nav_items["clip"].isChecked()

    def test_select_unknown_key_noop(self, win):
        win.select("nope")
        assert win._current == "clip"

    def test_pane_count_matches_nav(self, win):
        assert win.stack.count() == len(NAV_DEF)

    def test_only_one_checked_at_a_time(self, win):
        for key, *_ in NAV_DEF:
            win.select(key)
            checked = [k for k, it in win._nav_items.items() if it.isChecked()]
            assert checked == [key]

    def test_pane_factory_override(self, qapp):
        from PySide6.QtWidgets import QWidget
        from kivo.ui import main_window
        custom_pane = QWidget()
        win = MainWindow(Theme(False),
                         services={"pane_factory": lambda k: custom_pane if k == "ai" else None})
        assert win._panes["ai"] is custom_pane
        # 未覆盖的仍是占位
        assert isinstance(win._panes["clip"], main_window.PlaceholderPane)
