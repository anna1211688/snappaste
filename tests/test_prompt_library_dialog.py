# -*- coding: utf-8 -*-
"""提示词库数据层与弹窗测试。"""
import pytest
from PySide6.QtWidgets import QWidget

from kivo.core import prompt_store
from kivo.ui.dialogs.prompt_library_dialog import PromptLibraryDialog


@pytest.fixture
def parent(qapp):
    return QWidget()


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "prompts.json")


def test_load_builtin(path):
    items = prompt_store.load_library(path)
    assert len(items) == len(prompt_store.BUILTIN_PROMPTS)


def test_sanitize():
    assert prompt_store.sanitize_item({"title": " t ", "prompt": " p "}) == {
        "title": "t", "prompt": "p"}
    assert prompt_store.sanitize_item({"title": "", "prompt": "p"}) is None
    assert prompt_store.sanitize_item("x") is None


def test_add(path):
    items = prompt_store.load_library(path)
    assert prompt_store.add_item(items, "新角色", "新提示")
    assert items[-1]["title"] == "新角色"


def test_add_bad(path):
    items = []
    assert not prompt_store.add_item(items, "", "p")


def test_add_limit():
    items = [{"title": f"t{i}", "prompt": "p"} for i in range(prompt_store.LIB_MAX)]
    assert not prompt_store.add_item(items, "x", "y")


def test_delete():
    items = [{"title": "a", "prompt": "p"}, {"title": "b", "prompt": "p"}]
    assert prompt_store.delete_item(items, 0)
    assert items[0]["title"] == "b"
    assert not prompt_store.delete_item(items, 9)


def test_dialog_render(qapp, parent, path):
    d = PromptLibraryDialog(parent, path)
    d.show()
    qapp.processEvents()
    assert d.list.count() == len(prompt_store.BUILTIN_PROMPTS)


def test_dialog_apply(qapp, parent, path):
    chosen = []
    d = PromptLibraryDialog(parent, path, apply_callback=lambda x: chosen.append(x))
    d.list.setCurrentRow(0)
    d._apply()
    assert len(chosen) == 1
    assert chosen[0]["title"] == prompt_store.BUILTIN_PROMPTS[0]["title"]


def test_dialog_delete(qapp, parent, path):
    d = PromptLibraryDialog(parent, path)
    d.list.setCurrentRow(0)
    d._delete()
    qapp.processEvents()
    assert d.list.count() == len(prompt_store.BUILTIN_PROMPTS) - 1


def test_dialog_clear(qapp, parent, path):
    cleared = []
    d = PromptLibraryDialog(parent, path, clear_callback=lambda: cleared.append(1))
    d._clear()
    assert cleared == [1]


def test_dialog_add(qapp, parent, path, monkeypatch):
    d = PromptLibraryDialog(parent, path)
    before = d.list.count()

    class FakeEdit:
        def exec(self):
            return True

        def values(self):
            return "自定义角色", "自定义提示内容"

    monkeypatch.setattr(
        "kivo.ui.dialogs.prompt_library_dialog.PromptEditDialog",
        lambda p: FakeEdit())
    d._add()
    qapp.processEvents()
    assert d.list.count() == before + 1
