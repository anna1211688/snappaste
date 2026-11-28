# -*- coding: utf-8 -*-
"""JSON 数据持久化: 主文件 + .bak 备份, 损坏自动回退, 原子写。"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

from .util import atomic_write, log_crash


def load_json(path: str, default: Any, validator=None):
    """读取 JSON; 主文件损坏回退 .bak; validator(obj) 可选, 返回 False 时视为损坏。"""
    for p in (path, path + ".bak"):
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    obj = json.loads(f.read())
                if validator is None or validator(obj):
                    return obj
            except Exception:
                continue
    return default


def save_json(path: str, obj: Any, where: str = "save-json"):
    """原子写主文件并同步 .bak; 失败留痕。"""
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    try:
        atomic_write(path, text)
        try:
            atomic_write(path + ".bak", text)
        except OSError:
            pass
    except Exception:
        log_crash(where, *sys.exc_info())
