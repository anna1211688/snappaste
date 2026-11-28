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

# 剪贴板面板
_TABLE.update({
    "clip.title": ("复制记录", "Clipboard Records"),
    "clip.search_ph": ("搜索记录…", "Search records…"),
    "clip.lock": ("锁定/解锁", "Lock / Unlock"),
    "clip.dedupe": ("去重", "Remove duplicates"),
    "clip.del_sel": ("删除选定", "Delete selected"),
    "clip.del_all": ("删除全部", "Delete all"),
    "clip.empty_title": ("还没有记录", "No records yet"),
    "clip.empty_sub": ("直接复制一段文字，或按 F1 截一张图即可开始",
                       "Copy some text, or press F1 to take a screenshot"),
    "clip.multi": ("多次复制 (加入队列)", "Multi-copy (add to queue)"),
    "clip.paste_next": ("顺序粘贴下一条", "Paste next in order"),
    "clip.paste_all": ("全部粘贴", "Paste all"),
    "clip.options": ("粘贴选项", "Paste options"),
    "clip.separator": ("记录间分隔", "Separator between records"),
    "clip.sep_enter": ("回车", "Enter"),
    "clip.sep_none": ("无分隔", "None"),
    "clip.interval": ("间隔(ms)", "Interval (ms)"),
})

# 常用语面板
_TABLE.update({
    "phrase.title": ("常用语", "Phrases"),
    "phrase.empty_title": ("还没有常用语", "No phrases yet"),
    "phrase.empty_sub": ("把常回的话存成一条，之后双击就能直接粘贴",
                         "Save a common reply, then double-click to paste it"),
    "phrase.hint": ("选中一条，内容会填进编辑区；改完点「保存修改」。双击列表可直接粘贴。",
                    "Select an item to edit its text, then save. Double-click to paste."),
    "phrase.paste": ("粘贴选中", "Paste selected"),
    "phrase.copy": ("复制选中", "Copy selected"),
    "phrase.from_clip": ("从剪贴板添加", "Add from clipboard"),
    "phrase.save": ("保存修改", "Save changes"),
})

# 画廊面板
_TABLE.update({
    "gallery.title": ("截图历史", "Screenshot History"),
    "gallery.del_all": ("删除全部", "Delete all"),
    "gallery.count_more": ("共 {total} 个（只显示最近 {limit} 个）",
                           "{total} items (showing the latest {limit})"),
    "gallery.count": ("共 {n} 个", "{n} items"),
    "gallery.empty_title": ("还没有截图", "No screenshots yet"),
    "gallery.empty_sub": ("按 F1 截一张，截完会自动存在这里",
                          "Press F1 to capture; it will be saved here"),
    "gallery.shot": ("截一张图", "Take a screenshot"),
    "gallery.pin": ("钉图", "Pin"),
    "gallery.delete": ("删除", "Delete"),
})

# 项目工作台
_TABLE.update({
    "project.new": ("新建项目", "New Project"),
    "project.search_ph": ("搜索项目…", "Search projects…"),
    "project.recent": ("最近项目", "Recent Projects"),
    "project.head": ("项目", "Project"),
    "project.del": ("删除项目", "Delete Project"),
    "project.from_tpl": ("从模板创建", "Create from a template"),
    "project.notes": ("笔记", "Notes"),
    "project.save_note": ("保存笔记", "Save Notes"),
    "project.todos": ("待办", "To-dos"),
    "project.todo_ph": ("添加一条待办，回车确认", "Add a to-do, press Enter"),
    "project.links": ("文件链接", "File Links"),
    "project.name": ("名称", "Name"),
    "project.url": ("URL 或路径", "URL or path"),
    "project.progress": ("已完成 {done}/{total}", "{done}/{total} done"),
    "project.untitled": ("未命名项目", "Untitled Project"),
})

# 项目模板（创建时按当前语言写入初始内容）
_TABLE.update({
    "tpl.office.title": ("通用办公写作", "General Office Writing"),
    "tpl.office.desc": ("覆盖总结、写作、润色与翻译，结论先行、结构清晰。",
                        "Summaries, writing, polishing and translation; conclusion first."),
    "tpl.office.todo1": ("明确本次写作的目标与读者", "Define the goal and audience"),
    "tpl.office.todo2": ("列出提纲，结论先行", "Outline with the conclusion first"),
    "tpl.office.todo3": ("完成初稿并润色校对", "Draft, polish and proofread"),

    "tpl.data.title": ("数据分析与可视化", "Data Analysis & Visualization"),
    "tpl.data.desc": ("读取表格与数据、核验统计口径，输出分析结论与图表建议。",
                      "Read data, verify metrics, and deliver insights and chart advice."),
    "tpl.data.todo1": ("确认数据来源与统计口径", "Confirm data sources and metrics"),
    "tpl.data.todo2": ("清洗数据并核对关键指标", "Clean data and check key indicators"),
    "tpl.data.todo3": ("输出结论与可视化建议", "Deliver insights and visualization advice"),

    "tpl.meeting.title": ("会议与信息复盘", "Meeting & Information Review"),
    "tpl.meeting.desc": ("会议纪要、决策与待办提取，跨聊天和文档追踪进展。",
                         "Minutes, decisions and to-dos; track progress across chats and docs."),
    "tpl.meeting.todo1": ("整理会议纪要与关键决策", "Compile minutes and key decisions"),
    "tpl.meeting.todo2": ("拆解待办并指定负责人和时间", "Break down to-dos with owners and dates"),
    "tpl.meeting.todo3": ("跟进各项进展直到关闭", "Follow up until items are closed"),

    "tpl.market.title": ("市场调研与竞品分析", "Market & Competitor Research"),
    "tpl.market.desc": ("行业与竞品调研，统一维度对比，输出结论与建议。",
                        "Industry and competitor research with consistent dimensions."),
    "tpl.market.todo1": ("确定调研范围与对比维度", "Define scope and comparison dimensions"),
    "tpl.market.todo2": ("收集行业与竞品资料", "Gather industry and competitor material"),
    "tpl.market.todo3": ("统一维度对比并输出建议", "Compare and deliver recommendations"),
})

# AI 助手面板
_TABLE.update({
    "ai.side.task": ("工作任务", "Work Tasks"),
    "ai.side.schedule": ("定时任务", "Scheduled Tasks"),
    "ai.side.skills": ("提示词技能", "Prompt Skills"),
    "ai.side.project": ("项目", "Projects"),
    "ai.side.create": ("AI 创作", "AI Creation"),
    "ai.side.cloud": ("云盘目录", "Cloud Drive"),
    "ai.new_chat": ("新对话", "New Chat"),
    "ai.search_ph": ("搜索对话…", "Search chats…"),
    "ai.recent": ("最近对话", "Recent Chats"),
    "ai.no_match": ("没有匹配的对话", "No matching chats"),
    "ai.no_chat": ("暂无对话，点击上方新建", "No chats yet; create one above"),
    "ai.title": ("AI 助手", "AI Assistant"),
    "ai.clear": ("清空对话", "Clear Chat"),
    "ai.empty_title": ("开始一段新对话", "Start a new conversation"),
    "ai.empty_sub": ("在下方输入问题，或点击右侧建议快速开始",
                     "Type below or pick a suggestion on the right"),
    "ai.input_ph": ("输入你的问题，Enter 发送，Shift+Enter 换行…",
                    "Type a question. Enter to send, Shift+Enter for a new line"),
    "ai.send": ("发送", "Send"),
    "ai.stop": ("停止", "Stop"),
    "ai.interrupted": ("（生成中断）", "(Generation interrupted)"),
    "ai.error": ("（出错了）：{msg}", "(Error): {msg}"),
    "ai.welcome": ("你好，我是 KIVO", "Hi, I'm KIVO"),
    "ai.welcome_sub": ("你的 AI 助手，可以帮你写作、编程、搜索信息、分析数据。",
                       "Your AI assistant for writing, coding, search and data analysis."),
    "ai.suggest_head": ("你可以这样做", "Try asking"),
    "ai.sug1.t": ("帮我写一份产品策划案", "Write a product plan"),
    "ai.sug1.s": ("包含用户分析和核心功能", "with user analysis and core features"),
    "ai.sug2.t": ("Python 报错排查", "Debug a Python error"),
    "ai.sug2.s": ("帮我看看这段代码哪里有问题", "find what is wrong with this code"),
    "ai.sug3.t": ("翻译这段英文", "Translate this English text"),
    "ai.sug3.s": ("并标注重点词汇", "and highlight key vocabulary"),
    "ai.sug4.t": ("生成会议纪要", "Generate meeting minutes"),
    "ai.sug4.s": ("提炼会议要点和待办", "extract key points and to-dos"),
})

# 文本翻译面板
_TABLE.update({
    "trans.title": ("文本翻译", "Text Translation"),
    "trans.source": ("源语言", "Source language"),
    "trans.auto": ("自动检测", "Auto-detect"),
    "trans.target": ("目标语言", "Target language"),
    "trans.use_ai": ("启用AI翻译", "Enable AI translation"),
    "trans.use_mini": ("启用迷你翻译", "Enable mini translation"),
    "trans.use_copy": ("启用复制即译", "Enable copy-to-translate"),
    "trans.source_text": ("原文", "Source"),
    "trans.target_text": ("译文", "Translation"),
    "trans.paste": ("粘贴原文", "Paste source"),
    "trans.copy_both": ("复制双语", "Copy both"),
    "trans.copy_target": ("复制译文", "Copy translation"),
    "trans.no_result": ("没拿到译文", "No translation returned"),
    "trans.failed": ("（翻译失败）", "(Translation failed)"),
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
