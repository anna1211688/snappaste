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

# 语音翻译面板
_TABLE.update({
    "voice.title": ("语音翻译", "Voice Translation"),
    "voice.sub": ("选择聊天软件导出的语音消息，自动转写成文字再翻译成目标语言。",
                  "Pick a voice message exported from a chat app; it is transcribed and translated."),
    "voice.original": ("原文（转写）", "Original (transcript)"),
    "voice.translated": ("译文", "Translation"),
    "voice.pick": ("选择音频文件", "Choose audio file"),
    "voice.no_file": ("未选择文件", "No file selected"),
    "voice.fmt": ("支持 OGG/Opus、M4A/AAC、MP3、WAV、WEBM、FLAC、AAC 等，单个不超过 25 MB。",
                  "Supports OGG/Opus, M4A/AAC, MP3, WAV, WEBM, FLAC, AAC; up to 25 MB each."),
    "voice.target": ("目标语言", "Target language"),
    "voice.model": ("转写模型", "Transcription model"),
    "voice.source": ("源语言(可选)", "Source language (optional)"),
    "voice.start": ("开始转写翻译", "Start transcription & translation"),
    "voice.result_ph": ("结果将显示在这里", "Result will appear here"),
    "voice.copied": ("已复制", "Copied"),
    "voice.no_file_err": ("请先选择一个音频文件。", "Please choose an audio file first."),
    "voice.uploading": ("正在上传并转写语音…", "Uploading and transcribing…"),
    "voice.no_key": ("还没填 AI 接口的 API Key：到「设置 → AI 模型中心」选服务、填 key。",
                     "No API key yet: go to Settings → AI Model Center, choose a service and enter the key."),
    "voice.translating": ("正在翻译…", "Translating…"),
    "voice.done": ("完成", "Done"),
    "voice.failed": ("失败：", "Failed: "),
})

# 计算器 / 快捷面板
_TABLE.update({
    "calc.history": ("计算历史", "History"),
    "calc.empty": ("暂无计算历史", "No calculation history"),
    "quick.search_ph": ("搜索剪贴板、常用语，或直接算算术…",
                        "Search clips and phrases, or do a quick calculation…"),
})

# 软件自检
_TABLE.update({
    "chk.title": ("软件自检", "Self-check"),
    "chk.wait": ("待检测", "Waiting"),
    "chk.running": ("检测中…", "Checking…"),
    "chk.start": ("开始自检", "Run self-check"),
    "chk.ok": ("正常", "Normal"),
    "chk.bad": ("异常", "Abnormal"),
    "chk.data": ("数据目录可写", "Data directory writable"),
    "chk.config": ("配置文件完好", "Config file intact"),
    "chk.records": ("记录数据完好", "Records intact"),
    "chk.ocr": ("OCR 识别引擎", "OCR engine"),
    "chk.translate": ("翻译通道", "Translation channel"),
    "chk.hotkey": ("全局热键", "Global hotkeys"),
    "chk.hotkey_missing": ("全局热键未注册", "Global hotkeys not registered"),
    "chk.hotkey_count": ("{n} 个已注册", "{n} registered"),
})

# 世界时钟
_TABLE.update({
    "clock.title": ("世界时钟", "World Clock"),
    "clock.edit": ("编辑城市", "Edit Cities"),
    "clock.local": ("本地", "Local"),
    "clock.convert_head": ("约时间换算", "Time Conversion"),
    "clock.peer_city": ("对方城市", "Their city"),
    "clock.my_time": ("我的时间", "My time"),
    "clock.convert": ("换算", "Convert"),
    "clock.time_fmt": ("时间格式：YYYY-MM-DD HH:MM", "Time format: YYYY-MM-DD HH:MM"),
    "clock.peer_local": ("对方当地时间：", "Their local time: "),
    "clock.edit_entry": ("城市编辑入口（待接入城市选择面板）",
                         "City edit entry (to be connected)"),
    "weekday.0": ("周一", "Mon"), "weekday.1": ("周二", "Tue"),
    "weekday.2": ("周三", "Wed"), "weekday.3": ("周四", "Thu"),
    "weekday.4": ("周五", "Fri"), "weekday.5": ("周六", "Sat"),
    "weekday.6": ("周日", "Sun"),
})

# 城市名（键由时区路径生成: city.<zone>）
_TABLE.update({
    "city.asia.shanghai": ("北京", "Beijing"),
    "city.asia.hong_kong": ("香港", "Hong Kong"),
    "city.asia.taipei": ("台北", "Taipei"),
    "city.asia.singapore": ("新加坡", "Singapore"),
    "city.asia.bangkok": ("曼谷", "Bangkok"),
    "city.asia.jakarta": ("雅加达", "Jakarta"),
    "city.asia.manila": ("马尼拉", "Manila"),
    "city.asia.tokyo": ("东京", "Tokyo"),
    "city.asia.seoul": ("首尔", "Seoul"),
    "city.asia.kolkata": ("孟买", "Mumbai"),
    "city.australia.sydney": ("悉尼", "Sydney"),
    "city.australia.melbourne": ("墨尔本", "Melbourne"),
    "city.pacific.auckland": ("奥克兰", "Auckland"),
    "city.asia.dubai": ("迪拜", "Dubai"),
    "city.europe.istanbul": ("伊斯坦布尔", "Istanbul"),
    "city.europe.moscow": ("莫斯科", "Moscow"),
    "city.africa.cairo": ("开罗", "Cairo"),
    "city.africa.johannesburg": ("约翰内斯堡", "Johannesburg"),
    "city.europe.london": ("伦敦", "London"),
    "city.europe.paris": ("巴黎", "Paris"),
    "city.europe.berlin": ("柏林", "Berlin"),
    "city.europe.rome": ("罗马", "Rome"),
    "city.america.new_york": ("纽约", "New York"),
    "city.america.toronto": ("多伦多", "Toronto"),
    "city.america.chicago": ("芝加哥", "Chicago"),
    "city.america.denver": ("丹佛", "Denver"),
    "city.america.los_angeles": ("洛杉矶", "Los Angeles"),
    "city.america.vancouver": ("温哥华", "Vancouver"),
    "city.america.sao_paulo": ("圣保罗", "Sao Paulo"),
})

# 时钟城市选择
_TABLE.update({
    "cset.title": ("选择世界时间城市", "Choose World Clock Cities"),
    "cset.hint": ("勾选要显示的城市（本地永远在第一张）",
                  "Check cities to show (local is always first)"),
    "cset.search_ph": ("搜索城市，如 Tokyo、Sydney", "Search cities, e.g. Tokyo, Sydney"),
    "cset.not_found": ("没找到这个城市，换个关键词试试",
                       "City not found; try another keyword"),
    "cset.max_msg": ("最多选 {n} 个城市（本地不算）",
                     "Choose at most {n} cities (excluding local)"),
    "cset.count": ("已选 {n} / {max}", "Selected {n} / {max}"),
    "cset.min_one": ("至少选一个城市", "Select at least one city"),
})

# 货币名（键为货币代码）
_TABLE.update({
    "currency.USD": ("美元", "US Dollar"),
    "currency.CNY": ("人民币", "Chinese Yuan"),
    "currency.HKD": ("港币", "Hong Kong Dollar"),
    "currency.EUR": ("欧元", "Euro"),
    "currency.GBP": ("英镑", "British Pound"),
    "currency.JPY": ("日元", "Japanese Yen"),
    "currency.KRW": ("韩元", "Korean Won"),
    "currency.TWD": ("新台币", "New Taiwan Dollar"),
    "currency.MOP": ("澳门元", "Macanese Pataca"),
    "currency.AUD": ("澳元", "Australian Dollar"),
    "currency.CAD": ("加元", "Canadian Dollar"),
    "currency.CHF": ("瑞士法郎", "Swiss Franc"),
    "currency.SGD": ("新加坡元", "Singapore Dollar"),
    "currency.NZD": ("新西兰元", "New Zealand Dollar"),
    "currency.THB": ("泰币", "Thai Baht"),
    "currency.MYR": ("马来西亚林吉特", "Malaysian Ringgit"),
    "currency.IDR": ("印尼盾", "Indonesian Rupiah"),
    "currency.PHP": ("菲律宾比索", "Philippine Peso"),
    "currency.VND": ("越南盾", "Vietnamese Dong"),
    "currency.INR": ("印度卢比", "Indian Rupee"),
    "currency.AED": ("阿联酋迪拉姆", "UAE Dirham"),
    "currency.SAR": ("沙特里亚尔", "Saudi Riyal"),
    "currency.RUB": ("俄罗斯卢布", "Russian Ruble"),
    "currency.BRL": ("巴西雷亚尔", "Brazilian Real"),
    "currency.MXN": ("墨西哥比索", "Mexican Peso"),
    "currency.ZAR": ("南非兰特", "South African Rand"),
    "currency.TRY": ("土耳其里拉", "Turkish Lira"),
    "currency.SEK": ("瑞典克朗", "Swedish Krona"),
    "currency.NOK": ("挪威克朗", "Norwegian Krone"),
    "currency.DKK": ("丹麦克朗", "Danish Krone"),
    "currency.PLN": ("波兰兹罗提", "Polish Zloty"),
})

# 汇率换算面板
_TABLE.update({
    "fx.title": ("汇率换算", "Currency Converter"),
    "fx.loading": ("正在获取最新汇率…", "Fetching latest rates…"),
    "fx.convert_head": ("货币换算", "Currency Conversion"),
    "fx.table_head": ("各币种汇率", "Exchange Rates"),
    "fx.base": ("基准", "Base"),
    "fx.col_currency": ("货币", "Currency"),
    "fx.col_code": ("代码", "Code"),
    "fx.col_rate": ("汇率", "Rate"),
    "fx.amount_num": ("金额填数字", "Enter a numeric amount"),
    "fx.updated": ("更新时间：", "Updated: "),
    "fx.source": ("数据来源：open.er-api.com（免费接口，每日更新）",
                  "Source: open.er-api.com (free, updated daily)"),
    "fx.fetch_failed": ("汇率获取失败：", "Failed to fetch rates: "),
    "fx.api_error": ("汇率接口返回异常", "Unexpected rates API response"),
})

# 窗口管理面板
_TABLE.update({
    "winman.title": ("窗口管理", "Window Manager"),
    "winman.hint": ("先点一下要管理的窗口（让它在前台），再回来点按钮；按钮作用于最近使用的外部窗口。",
                    "Focus the window you want to manage first, then use a button here."),
    "winman.win_only": ("窗口管理仅在 Windows 上可用。",
                        "Window management is only available on Windows."),
    "winman.topmost": ("置顶切换", "Toggle always-on-top"),
    "winman.op80": ("半透明 80%", "80% opacity"),
    "winman.op60": ("半透明 60%", "60% opacity"),
    "winman.opaque": ("恢复不透明", "Restore opacity"),
    "winman.left": ("左半屏", "Snap left"),
    "winman.right": ("右半屏", "Snap right"),
    "winman.center": ("居中", "Center"),
    "winman.none": ("没有可管理的窗口", "No window to manage"),
    "winman.failed": ("操作失败", "Operation failed"),
})

# 番茄钟面板
_TABLE.update({
    "pomo.focus": ("专注中", "Focusing"),
    "pomo.break": ("休息中", "On break"),
    "pomo.focus_min": ("专注(分钟)", "Focus (min)"),
    "pomo.break_min": ("休息(分钟)", "Break (min)"),
    "pomo.invalid": ("请输入有效分钟数", "Enter valid minutes"),
    "pomo.applied": ("已应用", "Applied"),
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
