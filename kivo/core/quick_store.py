# -*- coding: utf-8 -*-
"""快捷面板数据层: 安全算术求值与结果聚合。"""
from __future__ import annotations

import ast
import operator
import re

QUICK_MAX_RESULTS = 12
_MATH_RE = re.compile(r"[0-9+\-*/%().\s]+")

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def safe_eval_math(expr):
    """AST 白名单算术求值，只允许数字与 + - * / % ( ) . 空格；不合法返回 None。"""
    if not expr or not _MATH_RE.fullmatch(expr):
        return None

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("bad node")

    try:
        v = ev(ast.parse(expr, mode="eval"))
        return round(v, 10) if isinstance(v, float) else v
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
        return None


def collect(query, records, phrases, max_results=QUICK_MAX_RESULTS):
    """聚合数学结果、剪贴板记录、常用语，返回 (标签, 实际值) 列表。"""
    q = (query or "").strip().lower()
    out = []

    math_val = safe_eval_math(q)
    if math_val is not None:
        out.append(("= " + str(math_val), str(math_val)))

    for r in records:
        t = r.get("text", "") if isinstance(r, dict) else str(r)
        if not q or q in t.lower():
            out.append((t.replace("\n", " ")[:80], t))
        if len(out) >= max_results:
            break

    if len(out) < max_results:
        for p in phrases:
            t = str(p.get("text", "")) if isinstance(p, dict) else str(p)
            if not q or q in t.lower():
                out.append(("◆ " + t.replace("\n", " ")[:78], t))
            if len(out) >= max_results:
                break
    return out
