# -*- coding: utf-8 -*-
"""计算器数据层: 纯计算状态机 + 计算历史持久化。"""
from __future__ import annotations

import math

from . import data
from .paths import CALC_HISTORY_PATH

ERROR = "ERROR"  # 内部哨兵；显示层经 i18n 翻译为「错误/Error」
HIST_MAX = 50


def fmt(v):
    if isinstance(v, str) or math.isnan(v) or v in (float("inf"), float("-inf")):
        return ERROR
    if abs(v - round(v)) < 1e-12 and abs(v) < 1e16:
        return str(round(v))
    return f"{v:.10f}".rstrip("0").rstrip(".") or "0"


def apply(a, op, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "×":
        return a * b
    if op == "÷":
        if b == 0:
            raise ZeroDivisionError
        return a / b
    return b


class CalcStore:
    def __init__(self, history_path=None):
        self._hist_path = history_path or CALC_HISTORY_PATH
        self.display = "0"
        self.trail = ""
        self.acc = None
        self.op = None
        self.fresh = True
        self.history = self._load_history()

    # ---------- 输入 ----------
    def _cur(self):
        try:
            return float(self.display)
        except ValueError:
            return 0.0

    def _error(self):
        self.display = ERROR
        self.trail = ""
        self.acc = None
        self.op = None
        self.fresh = True

    def digit(self, d):
        d0 = self.display
        if self.fresh or d0 in ("0", ERROR):
            self.display = d
            self.fresh = False
        elif len(d0.replace("-", "").replace(".", "")) < 16:
            self.display = d0 + d

    def dot(self):
        d0 = self.display
        if self.fresh or d0 == ERROR:
            self.display = "0."
            self.fresh = False
        elif "." not in d0:
            self.display = d0 + "."

    def set_op(self, op):
        if self.display == ERROR:
            return
        v = self._cur()
        if self.acc is not None and self.op and not self.fresh:
            try:
                v = apply(self.acc, self.op, v)
            except ZeroDivisionError:
                self._error()
                return
            self.display = fmt(v)
        self.acc = v
        self.op = op
        self.fresh = True
        self.trail = f"{fmt(v)} {op}"

    def equals(self):
        if self.acc is None or not self.op or self.display == ERROR:
            return
        v = self._cur()
        try:
            r = apply(self.acc, self.op, v)
        except ZeroDivisionError:
            self._error()
            return
        expr = f"{fmt(self.acc)} {self.op} {fmt(v)}"
        self.trail = f"{expr} ="
        self.display = fmt(r)
        self.add_history(expr, fmt(r))
        self.acc = None
        self.op = None
        self.fresh = True

    def clear(self):
        self.display = "0"
        self.trail = ""
        self.acc = None
        self.op = None
        self.fresh = True

    def back(self):
        if self.fresh:
            return
        d0 = self.display[:-1]
        self.display = d0 if d0 not in ("", "-") else "0"

    def percent(self):
        if self.display == ERROR:
            return
        self.display = fmt(self._cur() / 100)
        self.fresh = True

    def negate(self):
        if self.display == ERROR:
            return
        v = self._cur()
        if v != 0:
            self.display = fmt(-v)

    # ---------- 历史 ----------
    def _load_history(self):
        rows = data.load_json(self._hist_path, [])
        return [h for h in rows if isinstance(h, dict) and "e" in h and "r" in h][:HIST_MAX]

    def add_history(self, expr, res):
        self.history.insert(0, {"e": expr, "r": res})
        del self.history[HIST_MAX:]
        self._save()

    def clear_history(self):
        self.history = []
        self._save()

    def pick_history(self, idx):
        if 0 <= idx < len(self.history):
            self.display = self.history[idx]["r"]
            self.trail = ""
            self.acc = None
            self.op = None
            self.fresh = True

    def _save(self):
        data.save_json(self._hist_path, self.history, where="calc-history")
