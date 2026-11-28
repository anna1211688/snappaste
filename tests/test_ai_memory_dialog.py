# -*- coding: utf-8 -*-
"""AI 记忆数据层与弹窗测试。"""
import pytest
from PySide6.QtWidgets import QWidget

from kivo.core import memory_store
from kivo.ui.dialogs.ai_memory_dialog import AiMemoryDialog


@pytest.fixture
def parent(qapp):
    return QWidget()


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "memory.json")


def test_load_empty(path):
    assert memory_store.load_memory(path) == []


def test_add(path):
    items = memory_store.load_memory(path)
    assert memory_store.add_memory(items, "我喜欢深色模式")
    assert items[0]["text"] == "我喜欢深色模式"


def test_add_empty(path):
    items = []
    assert not memory_store.add_memory(items, "   ")


def test_add_full():
    items = [{"text": f"x{i}", "ts": 0} for i in range(memory_store.MEM_MAX)]
    assert not memory_store.add_memory(items, "one more")


def test_delete():
    items = [{"text": "a", "ts": 0}, {"text": "b", "ts": 0}]
    assert memory_store.delete_memory(items, 0)
    assert items[0]["text"] == "b"
    assert not memory_store.delete_memory(items, 9)


def test_clear():
    items = [{"text": "a", "ts": 0}]
    memory_store.clear_memory(items)
    assert items == []


def test_system_text():
    out = memory_store.system_text([{"text": "偏好A"}], "记忆：")
    assert "偏好A" in out and out.startswith("记忆：")
    assert memory_store.system_text([], "h") == ""


def test_text_tokens():
    toks = memory_store.text_tokens("hello 世界")
    assert "hello" in toks and "世" in toks


def test_relevant():
    mems = [{"text": "我喜欢深色模式", "ts": 0}, {"text": "工作语言是英语", "ts": 0}]
    out = memory_store.relevant_memories(mems, "深色", 5)
    assert len(out) == 1 and out[0]["text"] == "我喜欢深色模式"


def test_relevant_no_hit():
    mems = [{"text": "aaa", "ts": 0}]
    assert memory_store.relevant_memories(mems, "zzz", 5) == []


def test_dialog_render(qapp, parent, path):
    d = AiMemoryDialog(parent, path)
    d.show()
    qapp.processEvents()
    assert d.list.count() == 0


def test_dialog_add(qapp, parent, path):
    d = AiMemoryDialog(parent, path)
    d.entry.setText("记住这条")
    d._add()
    qapp.processEvents()
    assert d.list.count() == 1


def test_dialog_delete(qapp, parent, path):
    d = AiMemoryDialog(parent, path)
    d.entry.setText("x"); d._add()
    d._delete()
    qapp.processEvents()
    assert d.list.count() == 0


def test_dialog_clear_confirm(qapp, parent, path):
    d = AiMemoryDialog(parent, path)
    d.entry.setText("x"); d._add()
    d._clear()  # 第一次：进入确认态，不清空
    assert d.list.count() == 1
    d._clear()  # 第二次：真清空
    assert d.list.count() == 0
