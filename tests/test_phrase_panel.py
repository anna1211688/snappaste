# -*- coding: utf-8 -*-
"""常用语数据层与面板测试。"""
import json

import pytest

from kivo.core.phrase_store import PhraseStore, MAX_PHRASES
from kivo.ui.theme import Theme
from kivo.ui.panels.phrase_panel import PhrasePanel


@pytest.fixture
def ps(tmp_path):
    return PhraseStore(str(tmp_path / "phrases.json"))


# ---------- PhraseStore ----------
def test_add_empty_rejected(ps):
    assert ps.add("   ") is False
    assert ps.add("有效") is True
    assert len(ps.phrases) == 1


def test_update_delete(ps):
    ps.add("a")
    assert ps.update(0, "b") is True
    assert ps.phrases[0]["text"] == "b"
    assert ps.delete(0) is not None
    assert ps.phrases == []


def test_move(ps):
    ps.add("a")
    ps.add("b")
    ps.move(0, 1)
    assert ps.phrases[0]["text"] == "b"


def test_limit(ps):
    for i in range(MAX_PHRASES + 5):
        ps.add("line%d" % i)
    assert len(ps.phrases) == MAX_PHRASES


def test_save_reload(ps):
    ps.add("持久化")
    ps.save()
    again = PhraseStore(ps.path)
    assert again.phrases[0]["text"] == "持久化"


def test_bad_entries_dropped(tmp_path):
    p = tmp_path / "p.json"
    p.write_text(json.dumps([
        {"text": "ok"}, {"text": "   "}, "notdict", {"no": "x"},
    ]), encoding="utf-8")
    s = PhraseStore(str(p))
    assert len(s.phrases) == 1


# ---------- PhrasePanel ----------
@pytest.fixture
def pp(qapp, ps):
    p = PhrasePanel(Theme(False), ps)
    p.show()
    qapp.processEvents()
    return p


def test_empty_state(pp):
    assert pp.empty.isVisible()
    assert not pp.listw.isVisible()


def test_add_refresh(pp, qapp):
    pp.editor.setPlainText("新常用语")
    pp.add()
    qapp.processEvents()
    assert pp.listw.count() == 1
    assert pp.empty.isHidden()


def test_select_fills_editor(pp, ps, qapp):
    ps.add("内容")
    pp.refresh()
    pp.listw.setCurrentRow(0)
    qapp.processEvents()
    assert pp.editor.toPlainText() == "内容"


def test_save_edit(pp, ps, qapp):
    ps.add("旧")
    pp.refresh()
    pp.listw.setCurrentRow(0)
    pp.editor.setPlainText("新")
    pp.save_edit()
    qapp.processEvents()
    assert ps.phrases[0]["text"] == "新"


def test_delete(pp, ps, qapp):
    ps.add("待删")
    pp.refresh()
    pp.listw.setCurrentRow(0)
    pp.delete()
    qapp.processEvents()
    assert ps.phrases == []


def test_copy_selected(pp, ps):
    ps.add("复制我")
    pp.refresh()
    pp.listw.setCurrentRow(0)
    pp.copy_selected()
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "复制我"
