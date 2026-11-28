# -*- coding: utf-8 -*-
"""剪贴板记录数据层与面板测试。"""

import pytest

from kivo.core.clip_store import ClipStore, MAX_RECORDS
from kivo.ui.theme import Theme
from kivo.ui.panels.clip_panel import ClipPanel


# ---------- ClipStore ----------
@pytest.fixture
def cs(tmp_path):
    return ClipStore(str(tmp_path / "records.json"))


def test_add_and_dedupe(cs):
    cs.add("hello")
    cs.add("hello")  # 重复不入
    cs.add("world")
    assert len(cs.records) == 2


def test_save_reload(cs):
    cs.add("持久化")
    cs.save()
    again = ClipStore(cs.path)
    assert again.records[0]["text"] == "持久化"


def test_toggle_lock(cs):
    cs.add("a")
    cs.toggle_lock(0)
    assert cs.records[0]["locked"] is True


def test_delete_locked_protected(cs):
    cs.add("a")
    cs.toggle_lock(0)
    assert cs.delete(0) is None
    assert len(cs.records) == 1


def test_delete_all_keeps_locked(cs):
    cs.add("a")
    cs.add("b")
    cs.toggle_lock(0)
    cs.delete_all()
    assert len(cs.records) == 1
    assert cs.records[0]["locked"] is True


def test_move(cs):
    cs.add("a")
    cs.add("b")
    cs.move(0, 1)
    assert cs.records[0]["text"] == "b"


def test_dedupe(cs):
    cs.records = [{"text": "x", "locked": False},
                  {"text": "x", "locked": False},
                  {"text": "y", "locked": False}]
    cs.dedupe()
    assert [r["text"] for r in cs.records] == ["x", "y"]


def test_record_limit(cs):
    for i in range(MAX_RECORDS + 5):
        cs.add("q%d" % i)
    assert len(cs.records) == MAX_RECORDS


# ---------- ClipPanel ----------
@pytest.fixture
def cp(qapp, cs):
    p = ClipPanel(Theme(False), cs)
    p.show()
    qapp.processEvents()
    return p


def test_empty_state(cp):
    assert cp.empty.isVisible()
    assert not cp.listw.isVisible()


def test_refresh_list(cp, cs, qapp):
    cs.add("第一条")
    cs.add("第二条")
    cp.refresh()
    qapp.processEvents()
    assert cp.listw.count() == 2
    assert cp._visible == [0, 1]


def test_search_filter(cp, cs, qapp):
    cs.add("苹果")
    cs.add("香蕉")
    cp.search.setText("苹果")
    cp.refresh()
    qapp.processEvents()
    assert cp.listw.count() == 1
    assert cp._visible == [0]


def test_panel_lock_and_delete(cp, cs, qapp):
    cs.add("可删除")
    cp.refresh()
    cp.listw.setCurrentRow(0)
    cp.delete_selected()
    qapp.processEvents()
    assert len(cs.records) == 0


def test_paste_next_advances(cp, cs):
    cs.add("one")
    cs.add("two")
    cp.paste_next()
    assert cs.paste_index == 1
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "one"


def test_paste_all(cp, cs):
    cs.add("a")
    cs.add("b")
    cp.paste_all()
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "a\nb"


def test_separator_none(cp, cs):
    cs.add("a")
    cs.add("b")
    cp.sep_combo.setCurrentIndex(2)  # none
    cp.paste_all()
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "ab"
