# -*- coding: utf-8 -*-
"""快捷面板数据层与 UI 测试。"""
from PySide6.QtCore import Qt

from kivo.core import quick_store
from kivo.ui.theme import Theme
from kivo.ui.panels.quick_panel import QuickPanel


def test_safe_eval_basic():
    assert quick_store.safe_eval_math("2+3") == 5
    assert quick_store.safe_eval_math("2*3") == 6
    assert quick_store.safe_eval_math("10/4") == 2.5
    assert quick_store.safe_eval_math("10%3") == 1
    assert quick_store.safe_eval_math("-5+2") == -3
    assert quick_store.safe_eval_math("(2+3)*4") == 20


def test_safe_eval_bad():
    assert quick_store.safe_eval_math("__import__('os')") is None
    assert quick_store.safe_eval_math("abc") is None
    assert quick_store.safe_eval_math("1/0") is None
    assert quick_store.safe_eval_math("") is None


def test_collect_math_first():
    out = quick_store.collect("2+2", [], [])
    assert out[0] == ("= 4", "4")


def test_collect_records():
    records = [{"text": "hello world"}, {"text": "goodbye"}]
    out = quick_store.collect("hello", records, [])
    assert len(out) == 1
    assert out[0][1] == "hello world"


def test_collect_empty_query():
    records = [{"text": "a"}]
    phrases = [{"text": "b"}]
    out = quick_store.collect("", records, phrases)
    assert len(out) == 2


def test_collect_max():
    records = [{"text": f"item{i}"} for i in range(20)]
    out = quick_store.collect("", records, [])
    assert len(out) == quick_store.QUICK_MAX_RESULTS


def test_panel_render(qapp):
    p = QuickPanel(Theme(False), [{"text": "abc"}], [])
    p.show()
    qapp.processEvents()
    assert p.list.count() == 1


def test_panel_refresh_on_type(qapp):
    p = QuickPanel(Theme(False), [{"text": "alpha"}, {"text": "beta"}], [])
    p.show()
    p.entry.setText("beta")
    qapp.processEvents()
    assert p.list.count() == 1
    assert p._results[0][1] == "beta"


def test_panel_keyboard_down(qapp):
    p = QuickPanel(Theme(False), [{"text": "a"}, {"text": "b"}], [])
    p.show()
    qapp.processEvents()
    assert p.list.currentRow() == 0
    p.keyPressEvent(_key(Qt.Key_Down))
    assert p.list.currentRow() == 1


def test_panel_pick_callback(qapp):
    picked = []
    p = QuickPanel(Theme(False), [{"text": "hello"}], [],
                   pick_callback=lambda v: picked.append(v))
    p.show()
    qapp.processEvents()
    p.pick()
    assert picked == ["hello"]


class _key:
    """构造一个仅含 key() 的最小按键事件替身。"""
    def __init__(self, key):
        self._k = key

    def key(self):
        return self._k
