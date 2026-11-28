# -*- coding: utf-8 -*-
"""项目数据层与工作台面板测试。"""
import pytest

from kivo.core.project_store import (
    ProjectStore, PROJECT_MAX, TODO_MAX, LINK_MAX, _sanitize,
)
from kivo.ui.theme import Theme
from kivo.ui.panels.project_panel import ProjectPanel


@pytest.fixture
def st(tmp_path):
    return ProjectStore(str(tmp_path / "projects.json"))


# ---------- ProjectStore ----------
def test_create_blank(st):
    p = st.create()
    assert p["title"] == "未命名项目"
    assert p["todos"] == []
    assert len(st.projects) == 1


def test_create_from_template(st):
    p = st.create("office")
    assert p["template"] == "office"
    assert len(p["todos"]) == 3
    assert p["notes"]


def test_create_limit(st):
    for i in range(PROJECT_MAX + 5):
        st.create(title="p%d" % i)
    assert len(st.projects) == PROJECT_MAX


def test_delete(st):
    p = st.create()
    st.delete(p["id"])
    assert st.projects == []


def test_notes(st):
    p = st.create()
    st.set_notes(p["id"], "我的笔记")
    assert st.get(p["id"])["notes"] == "我的笔记"


def test_todos_add_toggle_remove(st):
    p = st.create()
    assert st.add_todo(p["id"], "任务")
    assert not st.add_todo(p["id"], "  ")
    st.toggle_todo(p["id"], 0)
    assert st.get(p["id"])["todos"][0]["done"] is True
    st.remove_todo(p["id"], 0)
    assert st.get(p["id"])["todos"] == []


def test_todo_limit(st):
    p = st.create()
    for i in range(TODO_MAX + 5):
        st.add_todo(p["id"], "t%d" % i)
    assert len(st.get(p["id"])["todos"]) == TODO_MAX


def test_links(st):
    p = st.create()
    assert st.add_link(p["id"], "n", "https://x.com")
    assert not st.add_link(p["id"], "n", " ")
    st.remove_link(p["id"], 0)
    assert st.get(p["id"])["links"] == []


def test_link_limit(st):
    p = st.create()
    for i in range(LINK_MAX + 5):
        st.add_link(p["id"], "n%d" % i, "path%d" % i)
    assert len(st.get(p["id"])["links"]) == LINK_MAX


def test_sanitize_bad():
    assert _sanitize({"title": "x"}) is None
    s = _sanitize({"id": 1, "todos": "bad", "links": [{"path": "u"}]})
    assert s["id"] == 1
    assert s["todos"] == []
    assert s["links"][0]["kind"] == "url"


def test_persistence(st):
    p = st.create()
    st.save()
    again = ProjectStore(st.path)
    assert len(again.projects) == 1
    assert again.projects[0]["id"] == p["id"]


# ---------- ProjectPanel ----------
@pytest.fixture
def pp(qapp, st):
    p = ProjectPanel(Theme(False), st)
    p.show()
    qapp.processEvents()
    return p


def test_empty_render(pp):
    assert pp.current is None
    assert pp.head_title.text() == "项目"


def test_open_detail(pp, st, qapp):
    proj = st.create("office")
    pp.open(proj)
    qapp.processEvents()
    assert pp.current["id"] == proj["id"]
    assert pp.head_title.text() == "通用办公写作"
    assert pp.todo_holder.layout().count() == 3


def test_panel_todo_progress(pp, st, qapp):
    proj = st.create()
    pp.open(proj)
    st.add_todo(proj["id"], "唯一任务")
    pp._render_todos(st.get(proj["id"]))
    qapp.processEvents()
    assert pp.progress.text() == "已完成 0/1"


def test_delete_current(pp, st, qapp):
    proj = st.create()
    pp.open(proj)
    pp.delete_current()
    qapp.processEvents()
    assert pp.current is None
    assert st.projects == []


def test_list_filter(pp, st, qapp):
    st.create(title="苹果项目")
    st.create(title="香蕉项目")
    pp.search.setText("苹果")
    pp.refresh_list()
    qapp.processEvents()
    from PySide6.QtWidgets import QPushButton
    rows = [w for w in pp.list_holder.findChildren(QPushButton)
            if w.objectName() == "chatRow"]
    assert len(rows) == 1
