# -*- coding: utf-8 -*-
"""常用语管理 (phrases.json): 加载校验、增删改、排序、落盘。"""
from __future__ import annotations

from . import data
from .paths import PHRASES_PATH

MAX_PHRASES = 500
MAX_PHRASE_CHARS = 50000


class PhraseStore:
    def __init__(self, path: str = PHRASES_PATH):
        self.path = path
        self.phrases = self._load()

    def _load(self):
        raw = data.load_json(self.path, [], validator=lambda o: isinstance(o, list))
        out = []
        for d in raw[:MAX_PHRASES]:
            if isinstance(d, dict) and str(d.get("text", "")).strip():
                out.append({"text": str(d["text"])})
        return out

    def save(self):
        data.save_json(self.path, self.phrases[:MAX_PHRASES], where="save-phrases")

    def add(self, text):
        text = (text or "").strip()
        if not text:
            return False
        if len(text) > MAX_PHRASE_CHARS:
            text = text[:MAX_PHRASE_CHARS]
        if len(self.phrases) >= MAX_PHRASES:
            return False
        self.phrases.append({"text": text})
        return True

    def update(self, i, text):
        text = (text or "").strip()
        if 0 <= i < len(self.phrases) and text:
            self.phrases[i]["text"] = text
            return True
        return False

    def delete(self, i):
        if 0 <= i < len(self.phrases):
            return self.phrases.pop(i)
        return None

    def move(self, i, d):
        j = i + d
        if 0 <= i < len(self.phrases) and 0 <= j < len(self.phrases):
            self.phrases[i], self.phrases[j] = self.phrases[j], self.phrases[i]
            return j
        return None
