# -*- coding: utf-8 -*-
"""剪贴板记录管理 (records.json): 加载校验、CRUD、去重、锁定、限额、粘贴进度。"""
from __future__ import annotations

from . import data
from .paths import RECORDS_PATH
from .i18n import tr

MAX_RECORDS = 2000
MAX_RECORD_CHARS = 200000


class ClipStore:
    def __init__(self, path: str = RECORDS_PATH):
        self.path = path
        self.paste_index = 0
        self.records = self._load()

    def _load(self):
        raw = data.load_json(self.path, [], validator=lambda o: isinstance(o, list))
        out = []
        for r in raw:
            if isinstance(r, dict) and isinstance(r.get("text"), str):
                out.append({"text": str(r["text"]), "locked": bool(r.get("locked"))})
        return out

    def save(self):
        data.save_json(self.path, self.records, where="save-records")

    # ---------- 变更 ----------
    def add(self, text, dedupe=True):
        text = text.strip("\r\n")
        if not text:
            return
        if len(text) > MAX_RECORD_CHARS:
            text = text[:MAX_RECORD_CHARS] + tr("clip.truncated")
        if dedupe and any(r["text"] == text for r in self.records):
            return
        self.records.append({"text": text, "locked": False})
        while len(self.records) > MAX_RECORDS:
            idx = next((i for i, r in enumerate(self.records[:-1])
                        if not r["locked"]), None)
            if idx is None:
                self.records.pop()
                break
            del self.records[idx]
            if idx < self.paste_index:
                self.paste_index -= 1

    def toggle_lock(self, i):
        if 0 <= i < len(self.records):
            self.records[i]["locked"] = not self.records[i]["locked"]

    def delete(self, i):
        if 0 <= i < len(self.records) and not self.records[i]["locked"]:
            rec = self.records.pop(i)
            if i < self.paste_index:
                self.paste_index -= 1
            return rec
        return None

    def delete_all(self):
        self.records = [r for r in self.records if r["locked"]]
        self.paste_index = 0

    def move(self, i, d):
        j = i + d
        if 0 <= i < len(self.records) and 0 <= j < len(self.records):
            self.records[i], self.records[j] = self.records[j], self.records[i]
            return j
        return None

    def dedupe(self):
        seen, out = set(), []
        kept_before = 0
        for i, r in enumerate(self.records):
            if r["text"] not in seen:
                seen.add(r["text"])
                out.append(r)
                if i < self.paste_index:
                    kept_before += 1
        self.records = out
        self.paste_index = kept_before
