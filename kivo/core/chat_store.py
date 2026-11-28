# -*- coding: utf-8 -*-
"""AI 对话存档管理 (ai_chats.json): 加载校验、CRUD、限额、排序、落盘。"""
from __future__ import annotations

import time

from . import data
from .paths import AI_CHATS_PATH
from .i18n import tr

MAX_CHATS = 30
MAX_MESSAGES = 200
MAX_MESSAGE_CHARS = 60000


def _valid_message(m):
    return (isinstance(m, dict) and m.get("role") in ("user", "assistant")
            and isinstance(m.get("content"), str)
            and len(m["content"]) <= MAX_MESSAGE_CHARS)


def _sanitize_chat(c):
    if not isinstance(c, dict) or not isinstance(c.get("messages"), list):
        return None
    msgs = []
    for m in c["messages"][-MAX_MESSAGES:]:
        if _valid_message(m):
            item = {"role": m["role"], "content": m["content"]}
            if isinstance(m.get("image_path"), str):
                item["image_path"] = m["image_path"]
            ipl = m.get("image_paths")
            if isinstance(ipl, list):
                plist = [x for x in ipl if isinstance(x, str)][:9]
                if plist:
                    item["image_paths"] = plist
            msgs.append(item)
    if not msgs:
        return None
    sp = c.get("system_prompt")
    return {
        "id": c.get("id"), "title": str(
            c.get("title") or tr("ai.new_chat"))[:200],
        "updated": c.get("updated") or 0, "pin": 1 if c.get("pin") else 0,
        "messages": msgs, "system_prompt": sp if isinstance(sp, dict) else None}


class ChatStore:
    def __init__(self, path: str = AI_CHATS_PATH):
        self.path = path
        self.chats = self._load()

    def _load(self):
        raw = data.load_json(self.path, [], validator=lambda o: isinstance(o, list))
        out = []
        for c in raw[:MAX_CHATS]:
            clean = _sanitize_chat(c)
            if clean:
                out.append(clean)
        return out

    def save(self):
        data.save_json(self.path, self.chats[:MAX_CHATS], where="store-ai-chats")

    # ---------- 查询 ----------
    def get(self, cid):
        return next((c for c in self.chats if c["id"] == cid), None)

    def _sort(self):
        self.chats.sort(key=lambda c: (0 if c.get("pin") else 1,
                                       -(c.get("updated") or 0)))

    # ---------- 变更 ----------
    def add(self, chat):
        self.chats.insert(0, chat)
        self._sort()
        del self.chats[MAX_CHATS:]
        return chat

    def remove(self, cid):
        c = self.get(cid)
        if c:
            self.chats.remove(c)
        return c

    def rename(self, cid, title):
        c = self.get(cid)
        if c:
            c["title"] = str(title)[:200]

    def toggle_pin(self, cid):
        c = self.get(cid)
        if c:
            c["pin"] = 0 if c.get("pin") else 1
            self._sort()

    def persist(self, cid, history, system_prompt=None):
        """把一段历史写入对应对话 (新建则创建), 返回 cid。"""
        chat = self.get(cid)
        if chat is None:
            cid = int(time.time() * 1000)
            first = next((m["content"] for m in history if m["role"] == "user"),
                         tr("ai.new_chat"))
            chat = {"id": cid, "title": first.replace("\n", " ")[:18],
                    "updated": 0, "pin": 0, "messages": []}
            self.add(chat)
        chat["messages"] = [dict(m) for m in history][-MAX_MESSAGES:]
        if system_prompt is not None:
            chat["system_prompt"] = system_prompt
        chat["updated"] = time.time()
        self._sort()
        del self.chats[MAX_CHATS:]
        return cid
