# -*- coding: utf-8 -*-
"""JSON 数据持久化: 主文件 + .bak 备份, 损坏自动回退, 原子写。

写盘支持两种模式:
- 同步模式 (默认): save_json 立即写盘, 便于测试与脚本。
- 异步模式 (生产应用): set_async(True) 后, save_json 仅在当前线程做内存
  序列化, 真正的磁盘 I/O 交给后台守护线程, 并合并对同一文件的连续写,
  应用退出前调用 flush_all 确保全部落盘。
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from typing import Any

from .util import atomic_write, log_crash

# 连续写同一文件的合并窗口(秒); 停笔超过该时长才真正落盘
_COALESCE_SECONDS = 0.12
_FLUSH_TIMEOUT = 10.0


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


def _sync_save(path: str, text: str, where: str):
    """同步写主文件并同步 .bak; 失败留痕。"""
    try:
        atomic_write(path, text)
        try:
            atomic_write(path + ".bak", text)
        except OSError:
            pass
    except Exception:
        log_crash(where, *sys.exc_info())


class _AsyncScheduler:
    """单后台线程写盘器: 主线程序列化入队, 后台线程合并写、防抖。"""

    def __init__(self):
        self._pending: dict[str, tuple[str, str]] = {}
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._idle = threading.Event()
        self._idle.set()
        self._stop = False
        self._thread = threading.Thread(
            target=self._loop, name="kivo-save", daemon=True)
        self._thread.start()

    def schedule(self, path: str, obj: Any, where: str):
        # 纯 CPU 序列化放在调用线程, 避免跨线程共享可变对象
        text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            self._pending[path] = (text, where)
            self._idle.clear()
            self._wake.set()

    def _drain(self):
        with self._lock:
            items = self._pending
            self._pending = {}
        if items:
            for path, (text, where) in items.items():
                _sync_save(path, text, where)
        with self._lock:
            if not self._pending:
                self._idle.set()

    def _loop(self):
        while True:
            if not self._wake.wait(0.25):
                if self._stop:
                    self._drain()
                    return
            self._wake.clear()
            if self._stop:
                self._drain()
                return
            # 防抖: 一个完整合并窗口内没有新请求才落盘, 期间新请求会重置等待
            while self._wake.wait(_COALESCE_SECONDS):
                self._wake.clear()
                if self._stop:
                    self._drain()
                    return
            self._drain()

    def flush(self, timeout: float = _FLUSH_TIMEOUT) -> bool:
        end = time.time() + timeout
        self._wake.set()
        while time.time() < end:
            with self._lock:
                no_pending = not self._pending
            if no_pending and self._idle.is_set():
                return True
            time.sleep(0.005)
        return False

    def close(self):
        self.flush()
        self._stop = True
        self._wake.set()


# ---------- 模式控制 ----------
_async_mode = False
_scheduler: _AsyncScheduler | None = None
_mode_lock = threading.Lock()


def set_async(enabled: bool):
    """开启/关闭异步写盘; 关闭前先把已排队内容全部落盘。"""
    global _async_mode, _scheduler
    with _mode_lock:
        if enabled:
            if _scheduler is None:
                _scheduler = _AsyncScheduler()
            _async_mode = True
        else:
            if _async_mode and _scheduler is not None:
                _scheduler.flush()
            _async_mode = False


def flush_all(timeout: float = _FLUSH_TIMEOUT) -> bool:
    """阻塞等待所有排队写盘完成; 返回是否在超时内完成。"""
    if _scheduler is None:
        return True
    return _scheduler.flush(timeout)


def shutdown_async():
    """应用退出时调用: 最后落盘并停止后台线程。"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.close()
        _scheduler = None


def save_json(path: str, obj: Any, where: str = "save-json"):
    """写 JSON。异步模式下仅入队, 同步模式下立即写盘。"""
    if _async_mode and _scheduler is not None:
        _scheduler.schedule(path, obj, where)
        return
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    _sync_save(path, text, where)
