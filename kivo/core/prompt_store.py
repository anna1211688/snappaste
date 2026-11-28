# -*- coding: utf-8 -*-
"""角色 / 提示词库数据层。"""
from __future__ import annotations

from .data import load_json, save_json
from .i18n import tr

TITLE_MAX = 80
PROMPT_MAX = 4000
LIB_MAX = 100

# 内置角色中文 title -> i18n key（用户自定义角色不在此表，保持原文）
_ROLE_KEYS = {
    "通用助手": "role.general",
    "专业翻译": "role.translator",
    "代码审查": "role.code_review",
    "写作教练": "role.writing",
    "产品经理": "role.pm",
    "数据分析师": "role.analyst",
}


def role_title_label(title):
    """内置角色名按当前语言显示；自定义角色名原样返回。"""
    key = _ROLE_KEYS.get(title)
    return tr(key) if key else title

BUILTIN_PROMPTS = [
    {"title": "通用助手", "prompt": "你是一个乐于助人的 AI 助手，回答准确、条理清晰、语言简洁。"},
    {"title": "专业翻译", "prompt": "你是资深翻译，译文忠实原文、通顺自然，只输出译文，不添加解释。"},
    {"title": "代码审查", "prompt": "你是资深工程师，审查代码时指出缺陷、风险和可改进点，给出可直接使用的修改建议与示例代码。"},
    {"title": "写作教练", "prompt": "你是写作教练，帮用户打磨文章结构与表达，语言自然，保留作者原意。"},
    {"title": "产品经理", "prompt": "你是经验丰富的产品经理，擅长需求拆解、用户场景分析和方案权衡，输出结构化、可落地的建议。"},
    {"title": "数据分析师", "prompt": "你是数据分析师，分析问题时先澄清口径，结论基于证据，给出指标定义与分析步骤。"},
]


def sanitize_item(it):
    if not isinstance(it, dict):
        return None
    title = str(it.get("title", "")).strip()[:TITLE_MAX]
    prompt = str(it.get("prompt", "")).strip()[:PROMPT_MAX]
    if not title or not prompt:
        return None
    return {"title": title, "prompt": prompt}


def load_library(path):
    """读取词库；缺失/坏档回退内置角色并落盘。"""
    def valid(obj):
        return isinstance(obj, list) and any(
            sanitize_item(x) is not None for x in obj)

    raw = load_json(path, None, validator=valid)
    if raw is None:
        save_library(path, BUILTIN_PROMPTS)
        return [dict(x) for x in BUILTIN_PROMPTS]
    out = [s for x in raw[:LIB_MAX] if (s := sanitize_item(x))]
    return out or [dict(x) for x in BUILTIN_PROMPTS]


def save_library(path, items):
    save_json(path, items[:LIB_MAX], where="prompt-library")


def add_item(items, title, prompt):
    """校验后追加，返回是否成功。"""
    if len(items) >= LIB_MAX:
        return False
    s = sanitize_item({"title": title, "prompt": prompt})
    if s is None:
        return False
    items.append(s)
    return True


def delete_item(items, index):
    if 0 <= index < len(items):
        items.pop(index)
        return True
    return False
