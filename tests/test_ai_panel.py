# -*- coding: utf-8 -*-
"""ChatStore 与 AI 助手面板测试。"""
import json
import threading
import time

import pytest

from kivo.core.chat_store import ChatStore, MAX_CHATS, MAX_MESSAGES
from kivo.ui.theme import Theme
from kivo.ui.components import MessageActionBar
from kivo.ui.panels.ai_panel import AIPanel


class MockAI:
    def __init__(self, reply="这是回复"):
        self.reply = reply
        self.cancelled = threading.Event()

    def chat_messages(self, messages, max_tokens=2048, route="chat",
                      stream_callback=None, cancel_event=None):
        if stream_callback:
            for ch in self.reply:
                if cancel_event is not None and cancel_event.is_set():
                    return ""
                stream_callback(ch)
        return self.reply


@pytest.fixture
def store(tmp_path):
    return ChatStore(str(tmp_path / "chats.json"))


@pytest.fixture
def panel(qapp, store):
    theme = Theme(dark=False)
    p = AIPanel(theme, MockAI(), store)
    p.show()
    qapp.processEvents()
    return p


def _pump(panel, qapp, timeout=3.0):
    end = time.time() + timeout
    while panel.busy and time.time() < end:
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()


# ---------- ChatStore ----------
def test_store_load_empty(store):
    assert store.chats == []


def test_persist_creates_chat(store):
    cid = store.persist(None, [{"role": "user", "content": "你好"}])
    assert store.get(cid) is not None
    assert store.chats[0]["title"] == "你好"
    store.save()
    again = ChatStore(store.path)
    assert len(again.chats) == 1


def test_chat_limit(store):
    for i in range(MAX_CHATS + 5):
        store.persist(None, [{"role": "user", "content": f"q{i}"}])
    assert len(store.chats) == MAX_CHATS


def test_message_limit(store):
    msgs = [{"role": "user", "content": "x"} for _ in range(MAX_MESSAGES + 10)]
    cid = store.persist(None, msgs)
    assert len(store.get(cid)["messages"]) == MAX_MESSAGES


def test_pin_rename_remove(store):
    cid = store.persist(None, [{"role": "user", "content": "a"}])
    store.toggle_pin(cid)
    assert store.get(cid)["pin"] == 1
    store.rename(cid, "新名字")
    assert store.get(cid)["title"] == "新名字"
    store.remove(cid)
    assert store.get(cid) is None


def test_pin_sorted_first(store):
    c1 = store.persist(None, [{"role": "user", "content": "first"}])
    c2 = store.persist(None, [{"role": "user", "content": "second"}])
    store.toggle_pin(c1)
    assert store.chats[0]["id"] == c1


def test_bad_messages_dropped(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps([
        {"id": 1, "messages": [{"role": "user", "content": "ok"}]},
        {"id": 2, "messages": [{"role": "bad", "content": "x"}]},
        {"id": 3, "messages": "notalist"},
    ]), encoding="utf-8")
    s = ChatStore(str(p))
    assert len(s.chats) == 1
    assert s.chats[0]["id"] == 1


# ---------- AIPanel ----------
def test_initial_empty_state(panel):
    assert panel.empty_state.isVisible()
    assert panel.history == []


def test_new_chat_resets(panel, qapp):
    panel.input.setPlainText("问题")
    panel.send()
    _pump(panel, qapp)
    assert len(panel.history) == 2
    panel.new_chat()
    assert panel.history == []
    assert panel.empty_state.isVisible()


def test_send_adds_user_and_reply(panel, qapp, store):
    panel.input.setPlainText("你好")
    panel.send()
    _pump(panel, qapp)
    assert panel.history[0]["role"] == "user"
    assert panel.history[1]["role"] == "assistant"
    assert not panel.empty_state.isVisible()
    assert len(store.chats) == 1
    assert panel.send_btn.text() == "发送"


def test_empty_text_not_sent(panel, qapp):
    panel.input.setPlainText("   ")
    panel.send()
    _pump(panel, qapp)
    assert panel.history == []
    assert not panel.busy


def test_load_chat(panel, qapp, store):
    panel.input.setPlainText("第一条")
    panel.send()
    _pump(panel, qapp)
    cid = panel.cid
    panel.new_chat()
    panel.load_chat(cid)
    assert panel.cid == cid
    assert len(panel.history) == 2


def test_search_filter(panel, qapp):
    panel.input.setPlainText("苹果")
    panel.send()
    _pump(panel, qapp)
    panel.search.setText("香蕉")
    qapp.sendPostedEvents()
    qapp.processEvents()
    # 无匹配: 只保留空态提示, 无 chatRow
    rows = [w for w in panel.recent_holder.findChildren(type(panel.send_btn))
            if w.objectName() == "chatRow"]
    assert rows == []
    panel.search.setText("苹果")
    qapp.processEvents()
    rows = [w for w in panel.recent_holder.findChildren(type(panel.send_btn))
            if w.objectName() == "chatRow"]
    assert len(rows) == 1


def test_cancel_stops(panel, qapp):
    panel.ai = MockAI()
    panel.request_reply()
    panel.stop()
    _pump(panel, qapp)
    assert not panel.busy
    assert panel.send_btn.text() == "发送"


# ---------- MessageActionBar 组件 ----------
def test_action_bar_has_six_actions(qapp):
    bar = MessageActionBar()
    assert len(bar._buttons) == 6
    fired = []
    bar.action_triggered.connect(fired.append)
    bar._buttons["copy"].click()
    assert fired == ["copy"]


def test_feedback_mutually_exclusive(qapp):
    bar = MessageActionBar()
    bar._buttons["up"].click()
    assert bar.feedback_state() == "up"
    bar._buttons["down"].click()
    assert bar.feedback_state() == "down"
    assert not bar._buttons["up"].isChecked()


def test_feedback_toggle_off(qapp):
    bar = MessageActionBar()
    bar._buttons["up"].click()
    bar._buttons["up"].click()  # 再点取消
    assert bar.feedback_state() is None


def test_reset_feedback(qapp):
    bar = MessageActionBar()
    bar._buttons["up"].click()
    bar.reset_feedback()
    assert bar.feedback_state() is None


# ---------- 面板集成 ----------
def _send_one(panel, qapp, text="你好"):
    panel.input.setPlainText(text)
    panel.send()
    _pump(panel, qapp)


def _first_bar(panel):
    bars = panel.msg_holder.findChildren(MessageActionBar)
    assert bars
    return bars[0]


def test_bot_message_has_action_bar(panel, qapp):
    _send_one(panel, qapp)
    assert panel.msg_holder.findChildren(MessageActionBar)


def test_action_copy_to_clipboard(panel, qapp):
    _send_one(panel, qapp)
    bar = _first_bar(panel)
    bar._buttons["copy"].click()
    from PySide6.QtWidgets import QApplication
    assert QApplication.clipboard().text() == "这是回复"


def test_action_forward_to_input(panel, qapp):
    _send_one(panel, qapp)
    bar = _first_bar(panel)
    bar._buttons["forward"].click()
    assert panel.input.toPlainText() == "这是回复"


def test_action_speak_callback(panel, qapp):
    spoken = []
    panel._speak = lambda t: spoken.append(t)
    _send_one(panel, qapp)
    _first_bar(panel)._buttons["speak"].click()
    assert spoken == ["这是回复"]


def test_action_regenerate(panel, qapp):
    calls = []

    class Counting(MockAI):
        def chat_messages(self, messages, **kw):
            calls.append(1)
            return super().chat_messages(messages, **kw)

    panel.ai = Counting()
    _send_one(panel, qapp)
    assert len(calls) == 1
    _first_bar(panel)._buttons["regenerate"].click()
    _pump(panel, qapp)
    assert len(calls) == 2
    # 重新生成后仍是 user + assistant 两条
    assert [m["role"] for m in panel.history] == ["user", "assistant"]


def test_regenerate_ignored_when_busy(panel, qapp):
    panel.busy = True
    panel._regenerate()  # 不应抛异常, 也不改变历史
    assert panel.history == []
