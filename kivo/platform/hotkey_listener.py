# -*- coding: utf-8 -*-
"""全局热键监听: 把热键配置映射到动作回调，Windows 用 keyboard 包，非 Windows 降级。"""
from __future__ import annotations

from . import IS_WINDOWS
from ..core import hotkey_store as hs


def _default_add(hk, cb):
    """注册热键，返回句柄。非 Windows 返回占位句柄（不真正拦截按键）。"""
    if not IS_WINDOWS:
        return ("stub", hk)
    import keyboard
    try:
        return keyboard.add_hotkey(hk, cb, suppress=True)
    except Exception:
        return keyboard.add_hotkey(hk, cb)


def _default_remove(handle):
    if not IS_WINDOWS or handle is None:
        return
    import keyboard
    try:
        keyboard.remove_hotkey(handle)
    except Exception:
        pass


class HotkeyListener:
    def __init__(self, config, action_map, add=None, remove=None):
        self.config = config
        self.action_map = action_map
        self._add = add or _default_add
        self._remove = remove or _default_remove
        self._handles = []

    def bindings(self):
        """从配置与动作映射读出 [(hk, callback)]，跳过空热键和无回调项。"""
        out = []
        for section, key, _label in hs.HOTKEY_ACTIONS:
            hk = hs.normalize_hotkey(hs.current_value(self.config, section, key))
            cb = self.action_map.get((section, key))
            if hk and cb:
                out.append((hk, cb))
        return out

    def start(self):
        self.stop()
        for hk, cb in self.bindings():
            try:
                handle = self._add(hk, cb)
            except Exception:
                continue
            if handle is not None:
                self._handles.append(handle)

    def stop(self):
        for handle in self._handles:
            self._remove(handle)
        self._handles = []

    @property
    def active_count(self):
        return len(self._handles)
