# -*- coding: utf-8 -*-
"""AI 模型中心数据层: 模型档案 (ModelProfiles) 与任务路由的纯逻辑读写。"""
from __future__ import annotations

import json

from .ai import AI_PRESETS

PROFILE_MAX_MODELS = 500
MODEL_ID_MAX = 200

# 可在任务分配里指定的路由（与 Tk 任务分配一致，不含 voice）
ROUTE_DEFS = [
    ("RouteChat", "AI 聊天"),
    ("RouteVision", "看图翻译"),
    ("RouteAnnotate", "标注栏 AI"),
    ("RouteReply", "智能回复"),
    ("RouteText", "文本翻译"),
]


def empty_profiles():
    return {k: [] for k in AI_PRESETS}


def load_profiles(config):
    """读取 ModelProfiles -> {svc: [{"model","enabled"}]}；坏档/缺失返回空骨架。"""
    try:
        raw = config.get("AI", "ModelProfiles", fallback="{}") or "{}"
        data = json.loads(raw)
    except Exception:
        return empty_profiles()
    out = empty_profiles()
    if not isinstance(data, dict):
        return out
    for svc in AI_PRESETS:
        rows = data.get(svc, [])
        if not isinstance(rows, list):
            continue
        seen = set()
        for row in rows[:PROFILE_MAX_MODELS]:
            if not isinstance(row, dict):
                continue
            model = str(row.get("model", "")).strip()[:MODEL_ID_MAX]
            if not model or model in seen:
                continue
            seen.add(model)
            out[svc].append({"model": model, "enabled": bool(row.get("enabled", True))})
    return out


def write_profiles(config, profiles):
    """把档案序列化为 JSON 写入 config（不 save，由调用方处理）。"""
    config.set("AI", "ModelProfiles",
               json.dumps(profiles, ensure_ascii=False, separators=(",", ":")))


def add_model(profiles, svc, model):
    """给某服务商添加模型（去重、规整、截断），返回是否新增成功。"""
    if svc not in AI_PRESETS:
        return False
    model = str(model or "").strip()[:MODEL_ID_MAX]
    if not model:
        return False
    rows = profiles[svc]
    if any(x["model"] == model for x in rows):
        return False
    if len(rows) >= PROFILE_MAX_MODELS:
        return False
    rows.append({"model": model, "enabled": True})
    return True


def remove_model(profiles, svc, model):
    if svc not in AI_PRESETS:
        return False
    before = len(profiles[svc])
    profiles[svc] = [x for x in profiles[svc] if x["model"] != model]
    return len(profiles[svc]) != before


def toggle_model(profiles, svc, model):
    if svc not in AI_PRESETS:
        return False
    for x in profiles[svc]:
        if x["model"] == model:
            x["enabled"] = not x["enabled"]
            return True
    return False


def load_routes(config):
    """读取任务路由 -> {route_key: (svc, model)}；空/非法表示跟随当前服务。"""
    out = {}
    for rk, _label in ROUTE_DEFS:
        svc = (config.get("AI", rk, fallback="") or "").strip()
        model = (config.get("AI", rk + "Model", fallback="") or "").strip()[:MODEL_ID_MAX]
        if svc in AI_PRESETS:
            out[rk] = (svc, model)
        else:
            out[rk] = ("", "")
    return out


def save_routes(config, routes):
    """写入任务路由（不 save）。routes: {route_key: (svc, model)}；空 tuple=跟随。"""
    for rk, _label in ROUTE_DEFS:
        svc, model = routes.get(rk, ("", ""))
        if svc in AI_PRESETS:
            config.set("AI", rk, svc)
            config.set("AI", rk + "Model", model[:MODEL_ID_MAX])
        else:
            config.set("AI", rk, "")
            config.set("AI", rk + "Model", "")
