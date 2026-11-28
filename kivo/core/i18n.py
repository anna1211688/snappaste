# -*- coding: utf-8 -*-
"""界面国际化 (i18n): 集中式中英文字符串字典。

- 语言在启动时从 Config/Language (Chinese/English) 读取一次, 重启生效。
- 面向用户的文案统一用 tr("key") 获取; 带变量用 tr("key", name=...)。
- 发给 AI 的 system prompt、QSS、objectName、配置键不属于界面文案, 不在此维护。
"""
from __future__ import annotations

ZH = "zh"
EN = "en"

# Config.ini 里的语言值 -> 内部语言代码
_CONFIG_LANG = {"Chinese": ZH, "English": EN}

# 通用词 (跨面板复用)
_COMMON = {
    "search": ("搜索", "Search"),
    "save": ("保存", "Save"),
    "cancel": ("取消", "Cancel"),
    "ok": ("确定", "OK"),
    "delete": ("删除", "Delete"),
    "add": ("添加", "Add"),
    "new": ("新增", "New"),
    "copy": ("复制", "Copy"),
    "close": ("关闭", "Close"),
    "refresh": ("刷新", "Refresh"),
    "clear": ("清空", "Clear"),
    "edit": ("编辑", "Edit"),
    "none": ("无", "None"),
    "error": ("错误", "Error"),
    "paste": ("粘贴", "Paste"),
    "tools": ("工具", "Tools"),
    "settings": ("设置", "Settings"),
    "start": ("开始", "Start"),
    "reset": ("重置", "Reset"),
    "skip": ("跳过", "Skip"),
    "apply": ("应用", "Apply"),
    "pause": ("暂停", "Pause"),
    "done": ("完成", "Done"),
    "normal": ("正常", "Normal"),
    "abnormal": ("异常", "Abnormal"),
    "enable": ("启用", "Enable"),
    "disable": ("停用", "Disable"),
    "title": ("标题", "Title"),
    "name": ("名称", "Name"),
    "target": ("目标", "Target"),
    "source": ("源", "Source"),
    "language": ("语言", "Language"),
    "copied": ("已复制", "Copied"),
    "translating": ("翻译中…", "Translating…"),
    "downloading": ("下载中…", "Downloading…"),
    "processing": ("处理中…", "Processing…"),
    "checking": ("检测中…", "Checking…"),
    "testing": ("测试中…", "Testing…"),
    "loading": ("加载中…", "Loading…"),
    "move_up": ("上移", "Move up"),
    "move_down": ("下移", "Move down"),
    "second": ("秒", "sec"),
    "minute": ("分钟", "min"),
}

# 各功能命名空间: key -> (中文, English)
_TABLE: dict[str, tuple[str, str]] = {}
for _k, _pair in _COMMON.items():
    _TABLE[f"common.{_k}"] = _pair

# 导航 / 主窗口
_TABLE.update({
    "app.title": ("KIVO 启沃", "KIVO"),
    "nav.ai": ("AI 助手", "AI Assistant"),
    "nav.voice": ("语音翻译", "Voice Translate"),
    "nav.trans": ("翻译中心", "Translation"),
    "nav.clip": ("剪贴板", "Clipboard"),
    "nav.phrases": ("常用语", "Phrases"),
    "nav.fx": ("汇率换算", "Currency"),
    "nav.clock": ("世界时钟", "World Clock"),
    "nav.calc": ("计算器", "Calculator"),
    "nav.dl": ("无水印下载", "Downloader"),
    "nav.dev": ("开发者工具箱", "Developer Tools"),
    "nav.pomo": ("番茄钟", "Pomodoro"),
    "nav.winman": ("窗口管理", "Window Manager"),
    "nav.batch": ("图片批量处理", "Batch Image"),
    "main.placeholder_hint": ("该面板将在迁移中接入完整功能",
                              "Full features will be added to this panel"),
    "group.tools": ("工具", "Tools"),
})

MESSAGES: dict[str, dict[str, str]] = {
    ZH: {k: zh for k, (zh, _en) in _TABLE.items()},
    EN: {k: en for k, (_zh, en) in _TABLE.items()},
}

_current = ZH


def configure(config) -> None:
    """启动时根据 ConfigManager 初始化当前语言。"""
    val = config.get("Config", "Language", "Chinese")
    set_language(_CONFIG_LANG.get(val, ZH))


def set_language(lang: str) -> None:
    global _current
    _current = lang if lang in (ZH, EN) else ZH


def get_language() -> str:
    return _current


def register(pairs: dict[str, tuple[str, str]]) -> None:
    """把一组 (key -> (中文, English)) 注册进字典。"""
    for key, (zh, en) in pairs.items():
        MESSAGES[ZH][key] = zh
        MESSAGES[EN][key] = en


def tr(key: str, **kwargs) -> str:
    """取当前语言文案; 缺键回退中文再回退 key 本身。"""
    table = MESSAGES.get(_current, MESSAGES[ZH])
    text = table.get(key)
    if text is None:
        text = MESSAGES[ZH].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def all_keys() -> set[str]:
    return set(MESSAGES[ZH]) | set(MESSAGES[EN])


def missing_keys() -> dict[str, list[str]]:
    """返回各语言缺失的键。"""
    zh_keys = set(MESSAGES[ZH])
    en_keys = set(MESSAGES[EN])
    return {ZH: sorted(en_keys - zh_keys), EN: sorted(zh_keys - en_keys)}
