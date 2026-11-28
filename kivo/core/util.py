# -*- coding: utf-8 -*-
"""核心工具: 原子写、崩溃日志、密钥脱敏、ini 标量。从 Tkinter 版本平移, 逻辑保持一致。"""
from __future__ import annotations

import os
import re
import sys
import time
import traceback

from . import paths

_crash_seen: dict = {}


def log_crash(where, exc_type, exc, tb):
    """异常写进 crash.log; 同一错误 60 秒去重, 文件超 1MB 只留尾部。日志自身出错不影响程序。"""
    try:
        text = "".join(traceback.format_exception(exc_type, exc, tb)) if exc_type else str(exc)
        key = (where, text.strip().splitlines()[-1] if text.strip() else "")
        now = time.time()
        if now - _crash_seen.get(key, 0) < 60:
            return
        if len(_crash_seen) > 500:
            _crash_seen.clear()
        _crash_seen[key] = now
        try:
            p = paths.CRASH_LOG_PATH
            if os.path.exists(p) and os.path.getsize(p) > 1_000_000:
                with open(p, encoding="utf-8", errors="replace") as f:
                    tail = f.read()[-200_000:]
                atomic_write(p, tail)
        except OSError:
            pass
        with open(paths.CRASH_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} [{where}] =====\n{text}\n")
    except Exception:
        pass


def install_crash_logging():
    """装主线程/后台线程异常钩子 + faulthandler 原生崩溃记录。"""
    import threading

    def _sys_hook(exc_type, exc, tb):
        log_crash("main", exc_type, exc, tb)
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _sys_hook

    def _thr_hook(args):
        log_crash(f"thread:{getattr(args.thread, 'name', '?')}",
                  args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = _thr_hook
    try:
        import faulthandler
        np = os.path.join(paths.BASE, "crash_native.log")
        if os.path.exists(np) and os.path.getsize(np) > 2_000_000:
            with open(np, encoding="utf-8", errors="replace") as f:
                tail = f.read()[-200_000:]
            atomic_write(np, tail)
        fh = open(np, "a", encoding="utf-8")
        faulthandler.enable(file=fh)
        globals()["_faulthandler_file"] = fh
    except Exception:
        pass


def atomic_write(path, text):
    """原子写: 临时文件 flush+fsync 后 os.replace, 保证磁盘上永远是完整版本。"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        dfd = os.open(os.path.dirname(os.path.abspath(path)), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass


def redact_secrets(text):
    """抹掉文本中的密钥类内容 (Bearer / key= / api_key / sk-)。"""
    s = str(text or "")
    s = re.sub(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+={0,2}", "Bearer ***", s)
    s = re.sub(r"(?i)([?&]key=)[^&\s]+", r"\1***", s)
    s = re.sub(r"(?i)((?:api[-_]?key|secret|sign|token)[\"']?\s*[:=]\s*[\"']?)[^\"'\s,}]+",
               r"\1***", s)
    s = re.sub(r"sk-[A-Za-z0-9\-_]{8,}", "sk-***", s)
    return s


def redact_ai_detail(detail, secret=""):
    """AI 接口报错文案统一脱敏。"""
    s = str(detail or "")
    s = re.sub(r"(?i)(authorization\s*[:=]\s*)[^\r\n]+", r"\1***", s)
    s = re.sub(r"(?i)(bearer\s+)[^\s,;\"']+", r"\1***", s)
    s = re.sub(r"(?i)((?:api[-_ ]?key|access[-_ ]?token|token)\"?\s*[:=]\s*\"?)"
               r"[^\s,;\"}\]&]+", r"\1***", s)
    s = re.sub(r"(?i)([?&](?:key|api_key|token|access_token)=)[^&\s\"']+", r"\1***", s)
    s = re.sub(r"\b(sk-[A-Za-z0-9_\-]{6,}|AIza[A-Za-z0-9_\-]{10,}|ghp_[A-Za-z0-9]{12,})",
               "***", s)
    if secret:
        s = s.replace(secret, "***")
    return s


def ini_scalar(v):
    """配置值收成一行, 防换行注入/损坏 ini 结构。"""
    return " ".join(str(v).split())
