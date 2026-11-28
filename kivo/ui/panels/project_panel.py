# -*- coding: utf-8 -*-
"""项目工作台面板: 侧边项目列表、模板空态、笔记/待办/链接详情。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QTextEdit, QCheckBox,
)

from ..theme import Theme, add_shadow
from ..components import (
    PrimaryButton, SecondaryButton, SectionHeader, MutedLabel,
)
from ...core.project_store import PROJECT_TEMPLATES


class ProjectPanel(QWidget):
    def __init__(self, theme: Theme, project_store):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = project_store
        self.current = None

        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(12)
        root.addWidget(self._sidebar(), 0)
        root.addWidget(self._main(), 1)

    # ---------- 侧边栏 ----------
    def _sidebar(self):
        wrap = QFrame()
        wrap.setObjectName("pane")
        wrap.setFixedWidth(224)
        add_shadow(wrap, blur=22, alpha=28)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(14, 16, 14, 16)
        lay.setSpacing(8)

        new = PrimaryButton("＋ 新建项目")
        new.clicked.connect(lambda: self.open(self.store.create()))
        lay.addWidget(new)

        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索项目…")
        self.search.textChanged.connect(self.refresh_list)
        lay.addWidget(self.search)

        lay.addWidget(SectionHeader("最近项目"))
        self.list_holder = QWidget()
        self.list_lay = QVBoxLayout(self.list_holder)
        self.list_lay.setContentsMargins(0, 0, 0, 0)
        self.list_lay.setSpacing(3)
        self.list_lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_holder)
        lay.addWidget(scroll, 1)
        self.refresh_list()
        return wrap

    def refresh_list(self):
        while self.list_lay.count() > 1:
            it = self.list_lay.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()
        q = self.search.text().strip().lower()
        for p in self.store.projects:
            if q and q not in p["title"].lower():
                continue
            row = QPushButton(("📌 " if p["pin"] else "  ") + p["title"])
            row.setObjectName("chatRow")
            row.setCursor(Qt.PointingHandCursor)
            row.setProperty("selected", "true" if self.current and p["id"] == self.current["id"] else "false")
            row.clicked.connect(lambda _=False, pid=p["id"]: self.open(self.store.get(pid)))
            self.list_lay.insertWidget(self.list_lay.count() - 1, row)

    # ---------- 主区 ----------
    def _main(self):
        wrap = QFrame()
        wrap.setObjectName("pane")
        add_shadow(wrap, blur=22, alpha=28)
        outer = QVBoxLayout(wrap)
        outer.setContentsMargins(0, 0, 0, 0)

        top = QFrame()
        top.setFixedHeight(54)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(20, 10, 18, 10)
        self.head_title = QLabel("项目")
        self.head_title.setObjectName("title")
        tl.addWidget(self.head_title)
        tl.addStretch()
        del_btn = SecondaryButton("删除项目")
        del_btn.clicked.connect(self.delete_current)
        tl.addWidget(del_btn)
        outer.addWidget(top)

        line = QFrame()
        line.setObjectName("divider")
        line.setFixedHeight(1)
        outer.addWidget(line)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_lay = QVBoxLayout(self.content)
        self.content_lay.setContentsMargins(20, 16, 20, 20)
        self.content_lay.setSpacing(10)
        self.content_lay.addStretch()
        scroll.setWidget(self.content)
        outer.addWidget(scroll, 1)
        self.render_empty()
        return wrap

    def _clear_content(self):
        while self.content_lay.count() > 1:
            it = self.content_lay.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()
            elif it.layout():
                self._wipe_layout(it.layout())

    def _wipe_layout(self, layout):
        while layout.count():
            it = layout.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()
            elif it.layout():
                self._wipe_layout(it.layout())

    def render_empty(self):
        self._clear_content()
        head = QLabel("从模板创建")
        head.setObjectName("blockHead")
        self.content_lay.insertWidget(0, head)
        for tpl in PROJECT_TEMPLATES:
            card = QFrame()
            card.setObjectName("templateCard")
            card.setFixedHeight(92)
            card.setCursor(Qt.PointingHandCursor)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 14, 40, 12)
            cl.setSpacing(4)
            t = QLabel(tpl["title"])
            t.setObjectName("tplTitle")
            d = QLabel(tpl["desc"])
            d.setObjectName("tplDesc")
            d.setWordWrap(True)
            cl.addWidget(t)
            cl.addWidget(d)
            plus = QLabel("+")
            plus.setObjectName("tplPlus")
            plus.setParent(card)
            plus.move(0, 0)
            card.mousePressEvent = lambda _e, k=tpl["key"]: self.open(self.store.create(k))
            card.resizeEvent = lambda _e, pl=plus: pl.move(card.width() - 34, 28)
            self.content_lay.insertWidget(self.content_lay.count() - 1, card)

    def open(self, project):
        if project is None:
            return
        self.current = project
        self.head_title.setText(project["title"])
        self.refresh_list()
        self.render_detail()

    def delete_current(self):
        if self.current:
            pid = self.current["id"]
            self.store.delete(pid)
            self.current = None
            self.head_title.setText("项目")
            self.refresh_list()
            self.render_empty()

    def render_detail(self):
        self._clear_content()
        p = self.current
        i = [0]

        def section(text):
            lab = QLabel(text)
            lab.setObjectName("blockHead")
            self.content_lay.insertWidget(i[0], lab)
            i[0] += 1

        # 笔记
        section("笔记")
        notes = QTextEdit()
        notes.setObjectName("detailBox")
        notes.setPlainText(p["notes"])
        notes.setFixedHeight(140)
        self.content_lay.insertWidget(i[0], notes)
        i[0] += 1
        save_note = SecondaryButton("保存笔记")
        save_note.clicked.connect(lambda: self.store.set_notes(p["id"], notes.toPlainText()))
        self.content_lay.insertWidget(i[0], save_note)
        i[0] += 1

        # 待办
        section("待办")
        self.progress = QLabel("")
        self.progress.setObjectName("mutedLabel")
        todo_input_row = QHBoxLayout()
        todo_input = QLineEdit()
        todo_input.setPlaceholderText("添加一条待办，回车确认")
        todo_input.returnPressed.connect(
            lambda: self._add_todo(p["id"], todo_input, todo_holder))
        todo_input_row.addWidget(todo_input)
        self.content_lay.insertLayout(i[0], todo_input_row)
        i[0] += 1
        self.todo_holder = QWidget()
        self.todo_lay = QVBoxLayout(self.todo_holder)
        self.todo_lay.setContentsMargins(0, 0, 0, 0)
        self.todo_lay.setSpacing(4)
        self.content_lay.insertWidget(i[0], self.todo_holder)
        i[0] += 1
        self.content_lay.insertWidget(i[0], self.progress)
        i[0] += 1
        self._render_todos(p, self.todo_holder)

        # 链接
        section("文件链接")
        link_row = QHBoxLayout()
        link_name = QLineEdit()
        link_name.setPlaceholderText("名称")
        link_path = QLineEdit()
        link_path.setPlaceholderText("URL 或路径")
        add_link = SecondaryButton("添加")
        add_link.clicked.connect(lambda: self._add_link(p, link_name, link_path))
        link_row.addWidget(link_name)
        link_row.addWidget(link_path, 1)
        link_row.addWidget(add_link)
        self.content_lay.insertLayout(i[0], link_row)
        i[0] += 1
        self.link_holder = QWidget()
        self.link_lay = QVBoxLayout(self.link_holder)
        self.link_lay.setContentsMargins(0, 0, 0, 0)
        self.link_lay.setSpacing(4)
        self.content_lay.insertWidget(i[0], self.link_holder)
        self._render_links(p)

    def _add_todo(self, pid, todo_input, todo_holder):
        p = self.store.get(pid)
        if self.store.add_todo(pid, todo_input.text()):
            todo_input.clear()
            self._render_todos(p, todo_holder)

    def _render_todos(self, p, holder=None):
        holder = holder or self.todo_holder
        lay = holder.layout()
        while lay.count():
            it = lay.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()
        for idx, td in enumerate(p["todos"]):
            row = QHBoxLayout()
            cb = QCheckBox(td["text"])
            cb.setChecked(td["done"])
            cb.toggled.connect(lambda _on, i=idx: (self.store.toggle_todo(p["id"], i),
                                                    self._update_progress(p)))
            x = QPushButton("✕")
            x.setObjectName("iconBtn")
            x.setFixedWidth(28)
            x.clicked.connect(lambda _=False, i=idx: (self.store.remove_todo(p["id"], i),
                                                       self._render_todos(self.store.get(p["id"]))))
            row.addWidget(cb)
            row.addStretch()
            row.addWidget(x)
            lay.addLayout(row)
        self._update_progress(p)

    def _update_progress(self, p):
        done = sum(1 for t in p["todos"] if t["done"])
        self.progress.setText("已完成 %d/%d" % (done, len(p["todos"])))

    def _add_link(self, p, name_edit, path_edit):
        if self.store.add_link(p["id"], name_edit.text(), path_edit.text()):
            name_edit.clear()
            path_edit.clear()
            self._render_links(self.store.get(p["id"]))

    def _render_links(self, p):
        lay = self.link_holder.layout()
        while lay.count():
            it = lay.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()
        for idx, lk in enumerate(p["links"]):
            row = QHBoxLayout()
            name = QLabel(("🔗 " if lk["kind"] == "url" else "📄 ") + lk["name"])
            x = QPushButton("✕")
            x.setObjectName("iconBtn")
            x.setFixedWidth(28)
            x.clicked.connect(lambda _=False, i=idx: (self.store.remove_link(p["id"], i),
                                                       self._render_links(self.store.get(p["id"]))))
            row.addWidget(name)
            row.addStretch()
            row.addWidget(x)
            lay.addLayout(row)
