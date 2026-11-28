# -*- coding: utf-8 -*-
"""AI 长期记忆数据层: 存取、增删清空、system 上下文与相关性筛选。"""
from __future__ import annotations

import re

from .data import load_json, save_json

MEM_MAX = 100
TEXT_MAX = 500
SYSTEM_MAX = 4000


def _sanitize(it):
    if not isinstance(it, dict):
        return None
    tx = it.get("text")
    if not isinstance(tx, str) or not tx.strip():
        return None
    return {"text": tx.strip()[:TEXT_MAX], "ts": it.get("ts") or 0}


def load_memory(path):
    """读取记忆；坏档/缺失返回空表。"""
    raw = load_json(path, None, validator=lambda o: isinstance(o, list))
    if raw is None:
        return []
    out = [s for x in raw[:MEM_MAX] if (s := _sanitize(x))]
    return out


def save_memory(path, items):
    save_json(path, items[:MEM_MAX], where="ai-memory")


def add_memory(items, text):
    """校验后追加；空内容或已满返回 False。"""
    s = _sanitize({"text": text, "ts": 0})
    if s is None or len(items) >= MEM_MAX:
        return False
    import time
    s["ts"] = time.time()
    items.append(s)
    return True


def delete_memory(items, index):
    if 0 <= index < len(items):
        items.pop(index)
        return True
    return False


def clear_memory(items):
    items.clear()


def system_text(mems, head):
    """拼成 system 上下文，总长封顶。"""
    lines = [m.get("text", "") for m in (mems or [])
             if isinstance(m, dict) and m.get("text")]
    if not lines:
        return ""
    return (head + "\n" + "\n".join("- " + x for x in lines))[:SYSTEM_MAX]


def text_tokens(text):
    """轻量分词：拉丁词（≥2 字符）+ 中日韩单字。"""
    if not text:
        return set()
    words = set(re.findall(r"[a-z0-9]{2,}", text.lower()))
    words.update(ch for ch in text if "\u4e00" <= ch <= "\u9fff")
    return words


def relevant_memories(mems, question, top_n):
    """按词面重叠打分，返回最相关的前 top_n；无命中返回空。"""
    q = text_tokens(question)
    if not q:
        return list(mems[:top_n])
    scored = []
    for i, m in enumerate(mems):
        hit = len(q & text_tokens(m.get("text", "")))
        if hit > 0:
            scored.append((hit, i, m))
    if not scored:
        return []
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [m for _hit, _i, m in scored[:top_n]]
