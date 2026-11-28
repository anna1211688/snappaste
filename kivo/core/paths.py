# -*- coding: utf-8 -*-
"""路径与数据文件常量。

数据目录规则沿用 Tkinter 版本: 打包后数据进 %APPDATA%\\KIVO, 源码运行时在工程旁; 不使用临时解压目录。
"""
from __future__ import annotations

import os
import sys

APP_NAME = "KIVO"
VERSION = "1.8.0"  # Qt 全面重写大版本 (发布前可再调整)

if getattr(sys, "frozen", False):
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE = getattr(sys, "_MEIPASS", EXE_DIR)
    BASE = os.path.join(os.environ.get("APPDATA") or EXE_DIR, APP_NAME)
    try:
        os.makedirs(BASE, exist_ok=True)
    except OSError:
        BASE = EXE_DIR
else:
    BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    BUNDLE = BASE
    EXE_DIR = BASE

CONFIG_PATH = os.path.join(BASE, "Config.ini")
RECORDS_PATH = os.path.join(BASE, "records.json")
PHRASES_PATH = os.path.join(BASE, "phrases.json")
AI_CHATS_PATH = os.path.join(BASE, "ai_chats.json")
AI_MEMORY_PATH = os.path.join(BASE, "ai_memory.json")
AI_PROMPTS_PATH = os.path.join(BASE, "ai_prompts.json")
PROJECTS_PATH = os.path.join(BASE, "projects.json")
CALC_HISTORY_PATH = os.path.join(BASE, "calc_history.json")
CRASH_LOG_PATH = os.path.join(BASE, "crash.log")
