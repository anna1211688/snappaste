# -*- coding: utf-8 -*-
"""AI 助手面板: 三栏布局、流式气泡、后台线程、中断、对话存档与切换。"""
from __future__ import annotations

import threading
from typing import Optional

from PySide6.QtCore import Qt, QObject, Signal, QEvent, QSize
from PySide6.QtGui import QPainter, QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea,
    QTextEdit, QLineEdit, QApplication,
)

from .. import icons as iconlib
from ..theme import Theme, add_shadow
from ..components import (
    PrimaryButton, GhostButton, SectionHeader, MutedLabel, MessageActionBar,
    EmptyState,
)

# 侧边功能入口 (动作键, 图标, 文案), 行为由组装层经 side_actions 注入
SIDEBAR_ACTIONS = [
    ("task", "edit", "工作任务"),
    ("schedule", "clock", "定时任务"),
    ("skills", "blocks", "提示词技能"),
    ("project", "project", "项目"),
    ("create", "ai", "AI 创作"),
    ("cloud", "cloud", "云盘目录"),
]


# ---------- 跨线程信号 ----------
class WorkerSignals(QObject):
    token = Signal(str)
    finished = Signal(str)
    failed = Signal(str)


def avatar(blue: bool, size: int = 34) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2E7CF6" if blue else "#C9D2E0"))
    p.drawEllipse(0, 0, size, size)
    p.setBrush(QColor("white"))
    p.drawEllipse(int(size * 0.32), int(size * 0.28), int(size * 0.36), int(size * 0.36))
    p.drawRoundedRect(int(size * 0.24), int(size * 0.62), int(size * 0.52),
                      int(size * 0.26), 4, 4)
    p.end()
    return pix


class AvatarLabel(QLabel):
    def __init__(self, blue: bool):
        super().__init__()
        self.setPixmap(avatar(blue))


class AIPanel(QWidget):
    def __init__(self, theme: Theme, ai_client, chat_store, speak=None,
                 side_actions=None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.ai = ai_client
        self.store = chat_store
        self._speak = speak  # 可选 TTS 回调, 缺省安全降级
        self._side_actions = side_actions or {}
        self.history: list = []
        self.cid = None
        self.busy = False
        self._cancel: Optional[threading.Event] = None
        self._stream_bubble: Optional[QLabel] = None
        self._stream_text = ""

        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(14)
        root.addWidget(self._sidebar(), 0)
        root.addWidget(self._chat_pane(), 1)
        root.addWidget(self._suggest_pane(), 0)

    # ---------- 左栏 ----------
    def _sidebar(self):
        wrap = QFrame()
        wrap.setObjectName("pane")
        wrap.setFixedWidth(228)
        add_shadow(wrap, blur=22, alpha=28)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(14, 16, 14, 16)
        lay.setSpacing(10)

        new = PrimaryButton("新对话", icon_name="plus")
        new.clicked.connect(self.new_chat)
        lay.addWidget(new)

        # 功能入口 (参照豆包侧边菜单)
        self.side_menu = {}
        for key, icn, label in SIDEBAR_ACTIONS:
            b = QPushButton(label)
            b.setObjectName("sideMenu")
            b.setIcon(iconlib.icon(icn))
            b.setIconSize(QSize(18, 18))
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._on_side_action(k))
            self.side_menu[key] = b
            lay.addWidget(b)

        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索对话…")
        self.search.textChanged.connect(self.refresh_recent)
        lay.addWidget(self.search)

        lay.addWidget(SectionHeader("最近对话"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.recent_holder = QWidget()
        self.recent_lay = QVBoxLayout(self.recent_holder)
        self.recent_lay.setContentsMargins(0, 0, 0, 0)
        self.recent_lay.setSpacing(3)
        self.recent_lay.addStretch()
        scroll.setWidget(self.recent_holder)
        lay.addWidget(scroll, 1)
        self.refresh_recent()
        return wrap

    def refresh_recent(self):
        # 清空 (保留末尾 stretch)
        while self.recent_lay.count() > 1:
            item = self.recent_lay.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
        q = self.search.text().strip().lower()
        shown = 0
        for c in self.store.chats:
            if q and q not in c["title"].lower():
                continue
            row = QPushButton(c["title"])
            row.setObjectName("chatRow")
            row.setCursor(Qt.PointingHandCursor)
            if c.get("pin"):
                row.setIcon(iconlib.icon("pin"))
            row.setProperty("selected", "true" if c["id"] == self.cid else "false")
            row.clicked.connect(lambda _=False, cid=c["id"]: self.load_chat(cid))
            self.recent_lay.insertWidget(self.recent_lay.count() - 1, row)
            shown += 1
        if shown == 0:
            empty = MutedLabel("没有匹配的对话" if q else "暂无对话，点击上方新建")
            empty.setWordWrap(True)
            self.recent_lay.insertWidget(self.recent_lay.count() - 1, empty)

    # ---------- 中栏 ----------
    def _chat_pane(self):
        wrap = QFrame()
        wrap.setObjectName("pane")
        add_shadow(wrap, blur=22, alpha=28)
        outer = QVBoxLayout(wrap)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QFrame()
        top.setFixedHeight(54)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(20, 10, 18, 10)
        title = QLabel("AI 助手")
        title.setObjectName("title")
        tl.addWidget(title)
        tl.addStretch()
        clear = GhostButton("清空对话", icon_name="trash")
        clear.clicked.connect(self.new_chat)
        tl.addWidget(clear)
        outer.addWidget(top)

        line = QFrame()
        line.setObjectName("divider")
        line.setFixedHeight(1)
        outer.addWidget(line)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.msg_holder = QWidget()
        self.msg_holder.setObjectName("msgHolder")
        self.msg_lay = QVBoxLayout(self.msg_holder)
        self.msg_lay.setContentsMargins(20, 16, 20, 12)
        self.msg_lay.setSpacing(14)
        self.msg_lay.addStretch()
        scroll.setWidget(self.msg_holder)
        self.scroll = scroll
        outer.addWidget(scroll, 1)
        outer.addWidget(self._input_area())
        self.empty_state = self._build_empty_state()
        self.msg_lay.insertWidget(self.msg_lay.count() - 1, self.empty_state, 1)
        return wrap

    def _build_empty_state(self):
        return EmptyState(
            "ai", "开始一段新对话", "在下方输入问题，或点击右侧建议快速开始")

    def _update_empty(self):
        self.empty_state.setVisible(not self.history)

    def _add_bubble(self, role: str, text: str):
        row = QHBoxLayout()
        row.setSpacing(10)
        if role == "user":
            row.addStretch()
            bub = QFrame()
            bub.setObjectName("userBubble")
            bub.setMaximumWidth(430)
            bl = QVBoxLayout(bub)
            bl.setContentsMargins(14, 10, 14, 10)
            lab = QLabel(text)
            lab.setObjectName("userText")
            lab.setWordWrap(True)
            bl.addWidget(lab)
            row.addWidget(bub)
            row.addWidget(AvatarLabel(True), 0, Qt.AlignTop)
        else:
            row.addWidget(AvatarLabel(False), 0, Qt.AlignTop)
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(4)
            bub = QFrame()
            bub.setObjectName("botBubble")
            bub.setMaximumWidth(470)
            bl = QVBoxLayout(bub)
            bl.setContentsMargins(14, 10, 14, 10)
            lab = QLabel(text)
            lab.setObjectName("botText")
            lab.setWordWrap(True)
            lab.setTextFormat(Qt.RichText)
            bl.addWidget(lab)
            col.addWidget(bub)
            bar = MessageActionBar()
            bar.action_triggered.connect(
                lambda k, lb=lab: self._on_message_action(k, lb))
            col.addWidget(bar)
            row.addLayout(col)
            row.addStretch()
        self.msg_lay.insertLayout(self.msg_lay.count() - 1, row)
        self._scroll_bottom()
        return lab

    def _scroll_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _input_area(self):
        box = QWidget()
        bl = QVBoxLayout(box)
        bl.setContentsMargins(18, 8, 18, 14)
        card = QFrame()
        card.setObjectName("inputCard")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(8)

        self.input = QTextEdit()
        self.input.setObjectName("input")
        self.input.setPlaceholderText("输入你的问题，Enter 发送，Shift+Enter 换行…")
        self.input.setFixedHeight(52)
        self.input.installEventFilter(self)
        cl.addWidget(self.input)

        bottom = QHBoxLayout()
        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("send")
        self.send_btn.setFixedSize(72, 36)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setIcon(iconlib.icon("send"))
        self.send_btn.clicked.connect(self._on_send_clicked)
        bottom.addStretch()
        bottom.addWidget(self.send_btn)
        cl.addLayout(bottom)
        bl.addWidget(card)
        return box

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self.send()
                return True
        return super().eventFilter(obj, event)

    def _on_send_clicked(self):
        if self.busy:
            self.stop()
        else:
            self.send()

    # ---------- 交互 ----------
    def new_chat(self):
        if self.busy:
            return
        self.cid = None
        self.history = []
        self._clear_messages()
        self._update_empty()
        self.refresh_recent()

    def _clear_messages(self):
        while self.msg_lay.count() > 1:
            item = self.msg_lay.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._delete_layout(item.layout())

    def _delete_layout(self, layout):
        while layout.count():
            it = layout.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()
            elif it.layout():
                self._delete_layout(it.layout())

    def load_chat(self, cid):
        if self.busy:
            return
        c = self.store.get(cid)
        if not c:
            return
        self.cid = cid
        self.history = [dict(m) for m in c["messages"]]
        self._clear_messages()
        for m in self.history:
            self._add_bubble(m["role"], m["content"])
        self._update_empty()
        self.refresh_recent()

    def send(self):
        text = self.input.toPlainText().strip()
        if self.busy or not text:
            return
        self.input.clear()
        self.history.append({"role": "user", "content": text})
        self._add_bubble("user", text)
        self._update_empty()
        self.cid = self.store.persist(self.cid, self.history)
        self.refresh_recent()
        self.request_reply()

    def request_reply(self):
        self.busy = True
        self.send_btn.setText("停止")
        self.send_btn.setIcon(iconlib.icon("stop"))
        self._cancel = threading.Event()
        self._stream_text = ""
        self._stream_bubble = self._add_bubble("bot", "")

        signals = WorkerSignals()
        signals.token.connect(self._on_token)
        signals.finished.connect(self._on_finished)
        signals.failed.connect(self._on_failed)
        history = list(self.history)
        cancel = self._cancel

        def work():
            try:
                def on_token(piece):
                    signals.token.emit(piece)
                r = self.ai.chat_messages(
                    history, max_tokens=2048, route="chat",
                    stream_callback=on_token, cancel_event=cancel)
                signals.finished.emit(r or "")
            except Exception as e:
                signals.failed.emit(str(e))

        threading.Thread(target=work, daemon=True).start()

    def _on_token(self, piece):
        self._stream_text += piece
        if self._stream_bubble is not None:
            self._stream_bubble.setText(self._stream_text)
            self._scroll_bottom()

    def _on_finished(self, text):
        self.busy = False
        self.send_btn.setText("发送")
        self.send_btn.setIcon(iconlib.icon("send"))
        if self._stream_bubble is not None:
            self._stream_bubble.setText(text)
        if text:
            self.history.append({"role": "assistant", "content": text})
            self.store.persist(self.cid, self.history)
        self.refresh_recent()
        self._scroll_bottom()

    def _on_failed(self, msg):
        self.busy = False
        self.send_btn.setText("发送")
        self.send_btn.setIcon(iconlib.icon("send"))
        partial = self._stream_text.strip()
        if partial:
            partial += "\n（生成中断）"
            if self._stream_bubble is not None:
                self._stream_bubble.setText(partial)
            self.history.append({"role": "assistant", "content": partial})
            self.store.persist(self.cid, self.history)
        elif self._stream_bubble is not None:
            self._stream_bubble.setText(f"（出错了）：{msg}")
        self.refresh_recent()

    def stop(self):
        if self._cancel is not None:
            self._cancel.set()

    # ---------- 回复消息操作 ----------
    def _on_message_action(self, key, lab):
        text = lab.text()
        if key == "copy":
            QApplication.clipboard().setText(text)
        elif key == "speak" and self._speak:
            self._speak(text)
        elif key == "forward":
            self.input.setPlainText(text)
            self.input.setFocus()
        elif key == "regenerate":
            self._regenerate()

    def _regenerate(self):
        if self.busy:
            return
        if self.history and self.history[-1]["role"] == "assistant":
            self.history.pop()
            self._clear_messages()
            for m in self.history:
                self._add_bubble(m["role"], m["content"])
            self._update_empty()
            self.request_reply()

    def _on_side_action(self, key):
        fn = self._side_actions.get(key)
        if fn:
            fn()

    # ---------- 右栏 ----------
    def _suggest_pane(self):
        wrap = QWidget()
        wrap.setObjectName("transparentPane")
        wrap.setFixedWidth(268)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(12)

        wcard = QFrame()
        wcard.setObjectName("welcomeCard")
        wcl = QVBoxLayout(wcard)
        wcl.setContentsMargins(16, 14, 16, 16)
        wcl.setSpacing(4)
        h = QLabel("你好，我是 KIVO")
        h.setObjectName("title")
        d = MutedLabel("你的 AI 助手，可以帮你写作、编程、搜索信息、分析数据。")
        d.setWordWrap(True)
        wcl.addWidget(h)
        wcl.addWidget(d)
        lay.addWidget(wcard)

        lay.addWidget(SectionHeader("你可以这样做"))
        for ti, sub in [
            ("帮我写一份产品策划案", "包含用户分析和核心功能"),
            ("Python 报错排查", "帮我看看这段代码哪里有问题"),
            ("翻译这段英文", "并标注重点词汇"),
            ("生成会议纪要", "提炼会议要点和待办"),
        ]:
            c = QFrame()
            c.setObjectName("sugCard")
            c.setCursor(Qt.PointingHandCursor)
            cl = QVBoxLayout(c)
            cl.setContentsMargins(14, 11, 14, 11)
            cl.setSpacing(3)
            a = QLabel(ti)
            a.setObjectName("sugTitle")
            b = QLabel(sub)
            b.setObjectName("sugSub")
            b.setWordWrap(True)
            cl.addWidget(a)
            cl.addWidget(b)
            c.mousePressEvent = lambda _e, t=ti: self._use_suggestion(t)
            lay.addWidget(c)
        lay.addStretch()
        return wrap

    def _use_suggestion(self, text):
        self.input.setPlainText(text)
        self.input.moveCursor(self.input.textCursor().End)
        self.input.setFocus()
