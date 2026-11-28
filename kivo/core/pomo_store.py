# -*- coding: utf-8 -*-
"""番茄钟数据层: 专注/休息计时状态机，不依赖 UI。"""
from __future__ import annotations


def format_seconds(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def next_mode(mode):
    return "break" if mode == "focus" else "focus"


class PomoStore:
    def __init__(self, focus_min=25, break_min=5):
        self.focus_min = focus_min
        self.break_min = break_min
        self.mode = "focus"
        self.running = False
        self.remain = focus_min * 60
        self.on_advance = None  # 回调：模式切换时由 UI 注入提示音/通知

    @property
    def total_for_mode(self):
        return self.focus_min if self.mode == "focus" else self.break_min

    def toggle(self):
        self.running = not self.running
        return self.running

    def tick(self):
        """每秒推进一格；到点自动切换，返回是否发生了切换。"""
        if not self.running:
            return False
        self.remain -= 1
        if self.remain <= 0:
            self.advance()
            return True
        return False

    def reset(self):
        self.running = False
        self.remain = self.total_for_mode * 60

    def advance(self):
        self.mode = next_mode(self.mode)
        self.remain = self.total_for_mode * 60
        if self.on_advance:
            self.on_advance(self.mode)

    def apply_settings(self, focus_min, break_min):
        if not (1 <= focus_min <= 180 and 1 <= break_min <= 60):
            return False
        self.focus_min = focus_min
        self.break_min = break_min
        if not self.running:
            self.remain = self.total_for_mode * 60
        return True

    def display(self):
        return format_seconds(self.remain)
