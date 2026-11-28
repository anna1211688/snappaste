# -*- coding: utf-8 -*-
"""热键数据层: 动作清单、键名规范化、冲突检测、默认值与配置读写。"""
from __future__ import annotations

import re

# 编辑类动作默认热键（[HotKey] 段）
DEFAULT_HOTKEYS = {
    "HotKey8": "F6", "HotKey9": "F7", "HotKey10": "F8",
    "HotKey11": "F9", "HotKey12": "SHIFT+F9",
}
# 截图/贴图习惯键（[Snip] 段）
DEFAULT_SNIP_KEYS = {
    "SnipKey": "F1", "PinKey": "F3", "CopyKey": "F5", "TransKey": "F4",
    "ReplyKey": "SHIFT+F4", "MiniTransKey": "F10", "CopyTransKey": "F11",
    "DelayKey": "无", "ClosePinsKey": "无", "TogglePinsKey": "无",
    "RestorePinKey": "无", "ClickThroughKey": "无",
}
NONE = "无"

# (section, key, i18n key)；动作绑定在系统层，这里只描述配置项
HOTKEY_ACTIONS: list[tuple[str, str, str]] = [
    ("Config", "ShowHotKey", "hk.show_main"),
    ("Config", "QuickPanelKey", "hk.quick_panel"),
    ("Config", "SelectAiKey", "hk.select_ai"),
    ("HotKey", "HotKey1", "hk.select_all"),
    ("HotKey", "HotKey2", "hk.cut"),
    ("HotKey", "HotKey3", "hk.copy"),
    ("HotKey", "HotKey4", "hk.paste"),
    ("HotKey", "HotKey5", "hk.power_paste"),
    ("HotKey", "HotKey7", "hk.multi_cut"),
    ("HotKey", "HotKey8", "hk.multi_copy"),
    ("HotKey", "HotKey9", "hk.seq_paste"),
    ("HotKey", "HotKey10", "hk.paste_all"),
    ("HotKey", "HotKey11", "hk.del_last"),
    ("HotKey", "HotKey12", "hk.del_all"),
    ("Snip", "SnipKey", "hk.snip"),
    ("Snip", "PinKey", "hk.pin"),
    ("Snip", "CopyKey", "hk.snip_copy"),
    ("Snip", "TransKey", "hk.snip_trans"),
    ("Snip", "ReplyKey", "hk.reply"),
    ("Snip", "MiniTransKey", "hk.mini_trans"),
    ("Snip", "CopyTransKey", "hk.copy_trans"),
    ("Snip", "DelayKey", "hk.delay_snip"),
    ("Snip", "ClosePinsKey", "hk.close_pins"),
    ("Snip", "TogglePinsKey", "hk.toggle_pins"),
    ("Snip", "RestorePinKey", "hk.restore_pin"),
    ("Snip", "ClickThroughKey", "hk.click_through"),
    ("OCHotKey", "HotKey", "hk.global_toggle"),
]


def normalize_hotkey(raw):
    """'无'/空 -> None；其余统一为 keyboard 包格式，如 'ctrl+alt+v' / 'f6'。"""
    if not raw:
        return None
    s = raw.strip().lower().replace(" ", "").replace("＋", "+")
    if s in ("无", "none", "no", "-"):
        return None
    s = s.replace("control", "ctrl").replace("windows", "win").replace("window", "win")
    s = s.strip("+")
    if not re.fullmatch(r"[a-z0-9_+-]+", s):
        return None
    return s or None


def current_value(config, section, key):
    """读取配置里的热键显示值，缺失/None 归一为「无」。"""
    v = (config.get(section, key, fallback=NONE) or NONE).strip()
    return NONE if v in (NONE, "None", "") else v


def find_conflicts(pairs):
    """pairs=[((section,key), 热键)...] -> {热键: [(section,key)...]} 仅含共用冲突。"""
    seen: dict[str, list] = {}
    for action_key, hk in pairs:
        k = str(hk or "").strip().lower()
        if k:
            seen.setdefault(k, []).append(action_key)
    return {k: v for k, v in seen.items() if len(v) > 1}


def build_mapping(config):
    """从配置读出 { (section,key): 显示值 }。"""
    return {(s, k): current_value(config, s, k) for s, k, _ in HOTKEY_ACTIONS}


def apply_mapping(config, mapping):
    """把 { (section,key): 显示值 } 规范化后写回 config（不保存，由调用方 save）。
    返回写入的规范化条目 [( (section,key), hk|None )]。"""
    normalized = []
    for action_key, raw in mapping.items():
        hk = normalize_hotkey(raw)
        normalized.append((action_key, hk))
    conflicts = find_conflicts(normalized)
    # 后设生效：每组冲突保留最后一个，前面的清空
    for keys in conflicts.values():
        for action_key in keys[:-1]:
            normalized = [(ak, None if ak == action_key else hk) for ak, hk in normalized]
    for (section, key), hk in normalized:
        config.set(section, key, hk.upper() if hk else NONE)
    return normalized, conflicts


def default_mapping():
    """恢复预设用：返回 { (section,key): 显示值 }。"""
    m = {}
    for s, k, _ in HOTKEY_ACTIONS:
        m[(s, k)] = NONE
    for k, v in DEFAULT_HOTKEYS.items():
        m[("HotKey", k)] = v
    for k, v in DEFAULT_SNIP_KEYS.items():
        m[("Snip", k)] = v
    m[("Config", "ShowHotKey")] = "F2"
    return m
