# -*- coding: utf-8 -*-
"""窗口管理: Win32 ctypes 封装。非 Windows 平台安全降级（不可用）。"""
from __future__ import annotations

import sys

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes


class WindowManager:
    def __init__(self):
        self.last_foreign = None
        self._u32 = ctypes.windll.user32 if IS_WINDOWS else None

    @property
    def supported(self):
        return IS_WINDOWS

    def foreground_hwnd(self):
        if not IS_WINDOWS:
            return None
        try:
            hwnd = self._u32.GetForegroundWindow()
            return hwnd or None
        except OSError:
            return None

    def target_hwnd(self, foreground_is_self):
        """优先当前前台外部窗口；前台是自己时用最近记录的外部窗口。"""
        hwnd = self.foreground_hwnd()
        if hwnd and not foreground_is_self:
            self.last_foreign = hwnd
            return hwnd
        return self.last_foreign

    def toggle_topmost(self, hwnd):
        GWL_EXSTYLE, WS_EX_TOPMOST = -20, 0x8
        ex = self._u32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        on = not (ex & WS_EX_TOPMOST)
        HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
        flags = 0x0001 | 0x0002 | 0x0010 | 0x0040
        self._u32.SetWindowPos(hwnd, HWND_TOPMOST if on else HWND_NOTOPMOST,
                               0, 0, 0, 0, flags)
        return on

    def set_opacity(self, hwnd, alpha):
        GWL_EXSTYLE, WS_EX_LAYERED = -20, 0x80000
        ex = self._u32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if alpha >= 255:
            self._u32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex & ~WS_EX_LAYERED)
            return
        if not (ex & WS_EX_LAYERED):
            self._u32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)
        self._u32.SetLayeredWindowAttributes(hwnd, 0, int(alpha), 0x2)

    def _work_area(self, hwnd):
        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        class MONINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", RECT),
                        ("rcWork", RECT), ("dwFlags", ctypes.c_ulong)]

        try:
            mon = self._u32.MonitorFromWindow(hwnd, 2)
            mi = MONINFO()
            mi.cbSize = ctypes.sizeof(MONINFO)
            self._u32.GetMonitorInfoW(mon, ctypes.byref(mi))
            r = mi.rcWork
        except OSError:
            r = RECT()
            self._u32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)
        return r.left, r.top, r.right, r.bottom

    def _move(self, hwnd, x, y, w, h):
        self._u32.SetWindowPos(hwnd, 0, int(x), int(y), int(w), int(h), 0x0040)

    def snap(self, hwnd, side):
        x0, y0, x1, y1 = self._work_area(hwnd)
        full_w, full_h = x1 - x0, y1 - y0
        half_w = full_w // 2
        if side == "left":
            self._move(hwnd, x0, y0, full_w - half_w, full_h)
        elif side == "right":
            self._move(hwnd, x0 + half_w, y0, full_w - half_w, full_h)
        else:
            self._move(hwnd, x0 + half_w // 2, y0 + full_h // 4,
                       half_w, full_h // 2)
