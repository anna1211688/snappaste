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
    "clip.truncated": ("\n……(单条记录超长, 已截断)",
                       "\n……(record too long, truncated)"),
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
    "voice.bad_mime": ("不支持这个音频格式 (支持 {fmts})。",
                      "Unsupported audio format (supported: {fmts})."),
    "voice.file_read": ("读不到这个音频文件: {err}",
                       "Cannot read the audio file: {err}"),
    "voice.empty_file": ("这个音频文件是空的 (0 字节)。",
                        "The audio file is empty (0 bytes)."),
    "voice.too_big": ("音频超过转写接口 25 MB 的上限，请先裁剪或压缩。",
                     "The audio exceeds the 25 MB transcription limit; trim or compress it first."),
    "voice.http_fail": ("语音转写失败 (HTTP {code}): {detail}",
                      "Speech transcription failed (HTTP {code}): {detail}"),
    "voice.unreachable": ("连不上语音转写服务: {reason}",
                         "Cannot reach the speech transcription service: {reason}"),
    "voice.bad_json": ("转写服务返回的内容不是有效 JSON。",
                      "The transcription service returned invalid JSON."),
    "voice.empty_result": ("转写结果为空: 可能没有可识别的人声，或模型不被支持。",
                          "Empty transcription: no recognizable speech, or the model is not supported."),
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

# 迷你翻译窗
_TABLE.update({
    "mini.title": ("迷你翻译", "Mini Translate"),
    "mini.translating": ("翻译中…", "Translating…"),
    "mini.no_result": ("没拿到译文", "No translation returned"),
    "mini.failed": ("翻译失败", "Translation failed"),
    "mini.one_copied": ("译文已复制", "Translation copied"),
    "mini.both_copied": ("双语已复制", "Both copied"),
})

# 无水印下载面板
_TABLE.update({
    "dl.title": ("无水印下载", "Watermark-free Download"),
    "dl.support": ("支持 Instagram / Facebook / 小红书 / 抖音 / TikTok / B站 / 微博 / 快手 / YouTube / X 等，保存平台原文件（不带水印）。",
                   "Supports Instagram, Facebook, Xiaohongshu, Douyin, TikTok, Bilibili, Weibo, Kuaishou, YouTube and X; saves original files without watermarks."),
    "dl.url_ph": ("粘贴分享链接或整段分享文案", "Paste a share link or the whole share text"),
    "dl.paste": ("粘贴链接", "Paste link"),
    "dl.save_to": ("保存到", "Save to"),
    "dl.pick_folder": ("选择文件夹", "Choose folder"),
    "dl.cookie": ("使用 Chrome 登录状态（IG/FB 受限内容，需先关 Chrome）",
                  "Use Chrome login state (restricted IG/FB content; close Chrome first)"),
    "dl.ask": ("每次下载前选择保存位置；不勾选则一直保存到上面文件夹",
               "Choose a location each time; otherwise always save to the folder above"),
    "dl.parse": ("解析", "Parse"),
    "dl.start": ("开始下载", "Start download"),
    "dl.open_folder": ("打开文件夹", "Open folder"),
    "dl.initial": ("把分享链接粘贴进来，点「开始下载」。",
                   "Paste a share link, then click Start download."),
    "dl.col_title": ("标题", "Title"),
    "dl.col_site": ("平台", "Platform"),
    "dl.col_file": ("文件", "File"),
    "dl.copyright": ("请只下载自己有权使用的内容；未经授权搬运他人作品可能涉及版权与平台规则。",
                     "Only download content you have rights to; unauthorized use may violate copyright and platform rules."),
    "dl.pick_location": ("选择保存位置", "Choose save location"),
    "dl.need_url": ("先粘贴一条链接再开始", "Paste a link first"),
    "dl.downloading": ("下载中…", "Downloading…"),
    "dl.download_pct": ("下载中 {pct}%", "Downloading {pct}%"),
    "dl.untitled": ("(无标题)", "(Untitled)"),
    "dl.saved": ("已保存：", "Saved: "),
    "dl.failed": ("失败：", "Failed: "),
    "dl.missing_yt": ("缺少 yt-dlp 组件", "yt-dlp component is missing"),
    "dl.need_login": ("该内容可能需要登录：勾选「使用 Chrome 登录状态」并关闭 Chrome 后重试。",
                     "This content may require login: enable “Use Chrome login state”, close Chrome, and retry."),
    "dl.unsupported": ("该链接暂不支持，换一条帖子/视频的分享链接试试。",
                      "This link is not supported yet; try another post/video share link."),
})

# 图片批量处理面板
_TABLE.update({
    "batch.title": ("图片批量处理", "Batch Image Processing"),
    "batch.add_images": ("添加图片", "Add images"),
    "batch.remove_sel": ("移除选中", "Remove selected"),
    "batch.percent": ("缩放百分比", "Scale percentage"),
    "batch.max_side": ("最长边(0=不限)", "Longest edge (0 = no limit)"),
    "batch.output_fmt": ("输出格式", "Output format"),
    "batch.keep_fmt": ("保持原格式", "Keep original"),
    "batch.quality": ("JPG/WEBP 质量", "JPG/WEBP quality"),
    "batch.watermark": ("文字水印(留空不加)", "Text watermark (blank = none)"),
    "batch.out_folder": ("输出文件夹", "Output folder"),
    "batch.choose": ("选择", "Choose"),
    "batch.start": ("开始批量处理", "Start batch processing"),
    "batch.choose_images": ("选择图片", "Choose images"),
    "batch.choose_out": ("选择输出文件夹", "Choose output folder"),
    "batch.need_images": ("请先添加图片", "Add images first"),
    "batch.bad_params": ("缩放或质量参数有误", "Invalid scale or quality parameters"),
    "batch.processing": ("处理中 {i}/{total}", "Processing {i}/{total}"),
    "batch.done": ("批量处理完成：成功 {ok} 张", "Batch finished: {ok} succeeded"),
    "batch.failed_count": ("，失败 {n} 张", ", {n} failed"),
    "batch.image_filter": ("图片 (*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff)",
                           "Images (*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff)"),
})

# 开发者工具箱
_TABLE.update({
    "dev.title": ("开发者工具箱", "Developer Tools"),
    "dev.tab_ts": ("时间戳", "Timestamp"),
    "dev.tab_regex": ("正则测试", "Regex"),
    "dev.tab_unit": ("单位换算", "Unit Conversion"),
    "dev.ts_in": ("输入时间戳", "Enter timestamp"),
    "dev.ts_to_date": ("时间戳→日期", "Timestamp → Date"),
    "dev.date_to_ts": ("日期→时间戳", "Date → Timestamp"),
    "dev.bad_input": ("输入有误", "Invalid input"),
    "dev.pretty": ("格式化", "Format"),
    "dev.minify": ("压缩", "Minify"),
    "dev.json_fail": ("JSON 解析失败", "Invalid JSON"),
    "dev.regex_ph": ("正则表达式", "Regex pattern"),
    "dev.regex_go": ("测试匹配", "Test match"),
    "dev.regex_hits": ("{n} 处匹配: ", "{n} matches: "),
    "dev.regex_fail": ("正则表达式有误", "Invalid regex"),
    "dev.encode": ("编码", "Encode"),
    "dev.decode": ("解码", "Decode"),
    "dev.enc_fail": ("编码失败", "Encoding failed"),
    "dev.dec_fail": ("解码失败", "Decoding failed"),
    "dev.copied": ("已复制", "Copied"),
})

# 设置面板
_TABLE.update({
    "set.general": ("通用", "General"),
    "set.language": ("语言", "Language"),
    "set.restart": ("(重启后生效)", "(takes effect after restart)"),
    "set.appearance": ("外观", "Appearance"),
    "set.light": ("浅色", "Light"),
    "set.dark": ("深色", "Dark"),
    "set.wave": ("提示音（复制/粘贴成功时响一声）", "Sound (beep on copy/paste)"),
    "set.ai_center": ("AI 模型中心", "AI Model Center"),
    "set.trans_service": ("翻译服务", "Translation Service"),
    "set.hotkey": ("热键设置", "Hotkey Settings"),
    "set.mini": ("迷你窗口（复制/粘贴时自动悬浮）",
                 "Mini Window (auto popup on copy/paste)"),
    "set.mini_time": ("悬浮显示时间(秒, 0=不显示)",
                      "Popup duration (sec, 0 = no popup)"),
    "set.always": ("常显", "Always show"),
    "set.clip_history": ("剪贴板历史", "Clipboard History"),
    "set.clip_watch": ("自动记录复制的文字到剪贴板历史（自动去重，单条上限 20 万字，最多 2000 条）",
                       "Auto-record copied text (deduplicated; up to 200k chars each, 2000 items)"),
    "set.proxy": ("网络代理", "Network Proxy"),
    "set.follow_system": ("跟随系统(推荐)", "Use system (recommended)"),
    "set.manual": ("手动代理", "Manual proxy"),
    "set.direct": ("直连(不使用代理)", "Direct (no proxy)"),
    "set.proxy_addr": ("代理地址", "Proxy address"),
    "set.mirror": ("更新镜像", "Update Mirror"),
    "set.mirror_addr": ("镜像地址", "Mirror address"),
    "set.mirror_hint": ("留空 = 直连 GitHub；填写后优先走镜像，失败再回退。",
                        "Blank = direct to GitHub; a mirror is tried first, then falls back."),
    "set.bad_url": ("请输入合法的 http(s) 地址", "Enter a valid http(s) URL"),
    "set.mirror_saved": ("更新镜像已保存", "Update mirror saved"),
    "set.check_update": ("检查更新", "Check for Updates"),
    "set.not_checked": ("尚未检查", "Not checked yet"),
    "set.checking": ("正在检查更新…", "Checking for updates…"),
    "set.check_fail": ("检查失败，请检查网络后重试",
                       "Check failed; verify your network and retry"),
    "set.new_version": ("发现新版本：", "New version found: "),
    "set.view_page": ("查看发布页", "View release page"),
    "set.up_to_date": ("已是最新版本", "You are up to date"),
    "set.shot_history": ("截图历史", "Screenshot History"),
    "set.save_shots": ("保存历史截图", "Save history screenshots"),
    "set.keep_max": ("最多保留", "Keep up to"),
    "set.zhang": ("张", "items"),
})

# 取色器
_TABLE.update({
    "color.title": ("取色器", "Color Picker"),
    "color.pick": ("屏幕取色", "Pick from Screen"),
    "color.empty": ("还没有历史颜色，点「屏幕取色」开始",
                    "No history yet. Click “Pick from Screen” to start."),
})

# 二维码弹窗
_TABLE.update({
    "qr.title": ("二维码生成", "QR Code Generator"),
    "qr.ph": ("输入文本或链接…", "Enter text or a link…"),
    "qr.gen": ("生成二维码", "Generate QR Code"),
    "qr.copy_img": ("复制图片", "Copy Image"),
    "qr.save_img": ("保存图片", "Save Image"),
    "qr.save_title": ("保存二维码", "Save QR Code"),
    "qr.missing": ("缺少 qrcode 库，请先 pip install qrcode",
                  "The qrcode library is missing; run pip install qrcode first"),
})

# 划词翻译结果卡
_TABLE.update({
    "ct.title": ("复制即译", "Quick Translate"),
    "ct.copy_both": ("复制双语", "Copy Both"),
    "ct.copy_trans": ("复制译文", "Copy Translation"),
    "ct.fail": ("翻译失败：检查网络后重试",
                "Translation failed: check your network and retry"),
})

# AI 长期记忆弹窗
_TABLE.update({
    "mem.title": ("AI 长期记忆", "AI Long-Term Memory"),
    "mem.hint": ("保存希望 AI 长期记住的信息（偏好、背景、常用资料），每次聊天会自动带上，无关条目 AI 会自行忽略。",
                 "Save information you want the AI to remember long-term (preferences, background, common references). It is sent with every chat; the AI ignores irrelevant entries."),
    "mem.ph": ("输入要记住的内容，回车添加…",
               "Enter what to remember, press Enter to add…"),
    "mem.delete_sel": ("删除选中", "Delete Selected"),
    "mem.clear_all": ("清空全部", "Clear All"),
    "mem.confirm": ("再点一次确认", "Click again to confirm"),
})

# 角色 / 提示词库弹窗
_TABLE.update({
    "plib.new_prompt": ("新增提示词", "New Prompt"),
    "plib.prompt_ph": ("提示词内容…", "Prompt content…"),
    "plib.library_title": ("角色 / 提示词库", "Roles / Prompt Library"),
    "plib.apply_role": ("选用角色", "Use Role"),
    "plib.delete_sel": ("删除选中", "Delete Selected"),
    "plib.clear_role": ("清除角色", "Clear Role"),
})

# 内置角色名
_TABLE.update({
    "role.general": ("通用助手", "General Assistant"),
    "role.translator": ("专业翻译", "Professional Translator"),
    "role.code_review": ("代码审查", "Code Reviewer"),
    "role.writing": ("写作教练", "Writing Coach"),
    "role.pm": ("产品经理", "Product Manager"),
    "role.analyst": ("数据分析师", "Data Analyst"),
})

# 热键设置弹窗
_TABLE.update({
    "hk.none": ("无", "None"),
    "hkdlg.press": ("请按键…", "Press a key…"),
    "hkdlg.title": ("热键设置", "Hotkey Settings"),
    "hkdlg.hint": ("点「录入」后直接按组合键，Esc 取消；留空或「无」= 不启用。同一键设给多个功能时，后设生效、先设自动清空。",
                   "Click “Capture”, then press a combination; Esc cancels. Blank or “None” disables it. If one key is assigned to multiple actions, the latest wins and earlier ones are cleared."),
    "hkdlg.capture": ("录入", "Capture"),
    "hkdlg.clear": ("清除", "Clear"),
    "hkdlg.restore": ("恢复预设", "Restore Defaults"),
    "hkdlg.restored": ("已恢复预设，点应用生效",
                       "Defaults restored; click Apply to take effect"),
    "hkdlg.confirm_conflict": ("确认冲突，后设生效",
                               "Confirm conflict; latest wins"),
    "hkdlg.dup": ("存在重复热键，再点一次确认",
                  "Duplicate hotkeys; click again to confirm"),
    "hkdlg.saved": ("热键已保存并立即生效", "Hotkeys saved and active now"),
})

# 热键动作名
_TABLE.update({
    "hk.show_main": ("唤出主窗口", "Show Main Window"),
    "hk.quick_panel": ("快捷面板", "Quick Panel"),
    "hk.select_ai": ("划词 AI", "Word AI"),
    "hk.select_all": ("全选", "Select All"),
    "hk.cut": ("剪切", "Cut"),
    "hk.copy": ("复制", "Copy"),
    "hk.paste": ("粘贴", "Paste"),
    "hk.power_paste": ("强力粘贴", "Power Paste"),
    "hk.multi_cut": ("多次剪切", "Multi-Cut"),
    "hk.multi_copy": ("多次复制", "Multi-Copy"),
    "hk.seq_paste": ("顺序粘贴", "Sequential Paste"),
    "hk.paste_all": ("全部粘贴", "Paste All"),
    "hk.del_last": ("删除最后一条", "Delete Last Entry"),
    "hk.del_all": ("删除全部记录", "Delete All Records"),
    "hk.snip": ("区域截图", "Region Screenshot"),
    "hk.pin": ("贴剪贴板", "Pin Clipboard"),
    "hk.snip_copy": ("截图并复制", "Screenshot & Copy"),
    "hk.snip_trans": ("截图翻译", "Screenshot Translate"),
    "hk.reply": ("智能回复", "Smart Reply"),
    "hk.mini_trans": ("迷你翻译", "Mini Translate"),
    "hk.copy_trans": ("复制即译", "Quick Translate"),
    "hk.delay_snip": ("延时截图", "Delayed Screenshot"),
    "hk.close_pins": ("关闭所有贴图", "Close All Pins"),
    "hk.toggle_pins": ("隐藏/显示所有贴图", "Hide/Show All Pins"),
    "hk.restore_pin": ("恢复上次关闭的贴图", "Restore Last Closed Pin"),
    "hk.click_through": ("贴图鼠标穿透开关", "Pin Click-Through Toggle"),
    "hk.global_toggle": ("全局切换热键", "Global Toggle Hotkey"),
})

# 翻译服务设置弹窗
_TABLE.update({
    "ts.free": ("免费接口（无需密钥）", "Free API (no key needed)"),
    "ts.baidu": ("百度翻译开放平台", "Baidu Translate Open Platform"),
    "ts.youdao": ("有道翻译", "Youdao Translate"),
    "ts.google": ("谷歌翻译（Google Cloud）", "Google Translate (Google Cloud)"),
    "ts.title": ("翻译服务", "Translation Service"),
    "ts.app_id": ("APP ID", "APP ID"),
    "ts.secret": ("密钥", "Secret Key"),
    "ts.note": ("百度/有道到开放平台免费申请 APP ID 和密钥；谷歌只需填 API 密钥。密钥只存本机，没填或出错时自动用免费接口。",
                "Apply for a free APP ID and key on the Baidu/Youdao open platforms; Google only needs an API key. Keys are stored locally. If missing or failing, the free API is used automatically."),
    "ts.testing": ("测试中…", "Testing…"),
    "ts.test_btn": ("测试", "Test"),
    "ts.need_creds": ("先填 APP ID 和密钥", "Enter APP ID and key first"),
    "ts.need_google": ("先填 API 密钥", "Enter API key first"),
    "ts.test_ok": ("测试成功：", "Test succeeded: "),
    "ts.test_fail_empty": ("测试失败：没拿到译文",
                           "Test failed: no translation returned"),
    "ts.test_fail": ("测试失败：", "Test failed: "),
    "ts.saved": ("翻译服务已保存", "Translation service saved"),
})

# 标注编辑器
_TABLE.update({
    "anno.rect": ("矩形", "Rectangle"),
    "anno.ellipse": ("椭圆", "Ellipse"),
    "anno.arrow": ("箭头", "Arrow"),
    "anno.line": ("直线", "Line"),
    "anno.pen": ("画笔", "Pen"),
    "anno.text": ("文字", "Text"),
    "anno.seq": ("序号", "Number"),
    "anno.mosaic": ("马赛克", "Mosaic"),
    "anno.blur": ("模糊", "Blur"),
    "anno.window_title": ("标注 - 画完点「完成并钉图」",
                          "Annotation — click “Finish & Pin” when done"),
    "anno.line_width": ("线宽", "Line width"),
    "anno.undo": ("撤销", "Undo"),
    "anno.redo": ("重做", "Redo"),
    "anno.clear": ("清空标注", "Clear Annotations"),
    "anno.ocr": ("OCR 识别文字", "OCR Text"),
    "anno.scan": ("扫二维码/条码", "Scan QR/Barcode"),
    "anno.discard": ("放弃", "Discard"),
    "anno.save_only": ("只保存不钉图", "Save Without Pin"),
    "anno.save_as": ("另存为", "Save As"),
    "anno.copy": ("复制到剪贴板", "Copy to Clipboard"),
    "anno.pin": ("完成并钉图", "Finish & Pin"),
    "anno.text_title": ("文字标注", "Text Annotation"),
    "anno.text_prompt": ("输入文字:", "Enter text:"),
})

# AI 服务商显示名
_TABLE.update({
    "prov.zhipu": ("智谱 GLM-4V-Flash (免费)", "Zhipu GLM-4V-Flash (Free)"),
    "prov.bailian": ("阿里云百炼 Qwen-VL", "Alibaba Cloud Bailian Qwen-VL"),
    "prov.siliconflow": ("硅基流动 Qwen2.5-VL", "SiliconFlow Qwen2.5-VL"),
    "prov.openai": ("OpenAI GPT-4o", "OpenAI GPT-4o"),
    "prov.gemini": ("Google Gemini", "Google Gemini"),
    "prov.claude": ("Anthropic Claude", "Anthropic Claude"),
    "prov.deepseek": ("DeepSeek (深度求索)", "DeepSeek"),
    "prov.moonshot": ("Kimi (Moonshot)", "Kimi (Moonshot)"),
    "prov.volcengine": ("火山方舟 豆包", "Volcano Ark Doubao"),
    "prov.hunyuan": ("腾讯混元", "Tencent Hunyuan"),
    "prov.qianfan": ("百度千帆 文心", "Baidu Qianfan ERNIE"),
    "prov.xai": ("xAI Grok", "xAI Grok"),
    "prov.dots": ("Dots 点点 (免费体验)", "Dots (free trial)"),
    "prov.ollama": ("Ollama 本地/自建", "Ollama Local/Self-hosted"),
    "prov.custom": ("自定义 (OpenAI 兼容接口)", "Custom (OpenAI-compatible)"),
})

# 任务路由名
_TABLE.update({
    "route.chat": ("AI 聊天", "AI Chat"),
    "route.vision": ("看图翻译", "Image Translation"),
    "route.annotate": ("标注栏 AI", "Annotation AI"),
    "route.reply": ("智能回复", "Smart Reply"),
    "route.text": ("文本翻译", "Text Translation"),
})

# AI 模型中心弹窗
_TABLE.update({
    "ais.title": ("AI 模型中心", "AI Model Center"),
    "ais.save_all": ("保存全部设置", "Save All Settings"),
    "ais.provider": ("服务商", "Provider"),
    "ais.base": ("接口地址", "Base URL"),
    "ais.model": ("模型", "Model"),
    "ais.fetch": ("获取模型", "Fetch Models"),
    "ais.add": ("添加到模型列表", "Add to Model List"),
    "ais.available": ("可用模型", "Available Models"),
    "ais.use": ("选用", "Use"),
    "ais.provider_hint": ("每家服务商独立保存；OpenAI 兼容接口可自动获取模型，其他可手动填写。",
                          "Settings are saved separately per provider. OpenAI-compatible endpoints can fetch models automatically; others can be filled in manually."),
    "ais.provider_tab": ("服务商配置", "Provider"),
    "ais.fetch_fail": ("获取失败：", "Fetch failed: "),
    "ais.fetched_count": ("获取到 {n} 个模型", "Fetched {n} models"),
    "ais.need_id": ("请先填写模型 ID", "Enter a model ID first"),
    "ais.added": ("已添加：", "Added: "),
    "ais.model_exists": ("模型已存在", "Model already exists"),
    "ais.set_default": ("设为默认", "Set as Default"),
    "ais.toggle": ("启用/停用", "Enable/Disable"),
    "ais.delete_model": ("删除模型", "Delete Model"),
    "ais.models_tab": ("模型列表", "Model List"),
    "ais.enabled": ("启用", "Enabled"),
    "ais.disabled": ("停用", "Disabled"),
    "ais.default_set": ("已设为该服务商默认模型",
                        "Set as the default model for this provider"),
    "ais.routes_hint": ("为不同任务指定服务商；选「跟随当前服务」则用默认服务商。",
                       "Assign a provider to each task. “Follow current service” uses the default provider."),
    "ais.follow": ("跟随当前服务", "Follow current service"),
    "ais.routes_tab": ("任务分配", "Task Routing"),
    "ais.fallback": ("当前模型失败时自动尝试同服务商其他已启用模型",
                     "Automatically try other enabled models of the same provider when the current model fails"),
    "ais.test_hint": ("选择服务商并填写 Key、模型后，可在此测试连接。",
                      "Select a provider and fill in its key and model, then test the connection here."),
    "ais.test_provider": ("测试当前服务商", "Test Current Provider"),
    "ais.test_tab": ("连接测试", "Connection Test"),
    "ais.testing": ("测试中…", "Testing…"),
    "ais.conn_ok": ("连接正常 · {sec} 秒 · 返回：{r}",
                    "Connection OK · {sec} s · Reply: {r}"),
    "ais.conn_fail": ("连接失败 · {sec} 秒 · {e}",
                     "Connection failed · {sec} s · {e}"),
    "ais.empty_reply": ("空", "Empty"),
    "ais.saved": ("AI 模型中心已保存", "AI model center saved"),
})

# 贴图右键菜单
_TABLE.update({
    "pin.rotate": ("旋转 90°", "Rotate 90°"),
    "pin.opacity": ("透明度", "Opacity"),
    "pin.copy_img": ("复制图片", "Copy Image"),
    "pin.close": ("关闭贴图", "Close Pin"),
})

# 系统托盘
_TABLE.update({
    "tray.show": ("显示主窗口", "Show Main Window"),
    "tray.snip": ("区域截图", "Region Screenshot"),
    "tray.snip_copy": ("截图并复制", "Screenshot & Copy"),
    "tray.snip_trans": ("截图翻译", "Screenshot Translate"),
    "tray.snip_reply": ("智能回复", "Smart Reply"),
    "tray.mini": ("迷你翻译", "Mini Translate"),
    "tray.pin": ("贴剪贴板内容", "Pin Clipboard Content"),
    "tray.tooltip": ("KIVO 智能工作台", "KIVO Smart Workbench"),
    "tray.quit": ("退出 KIVO", "Quit KIVO"),
})

# AI 客户端错误消息
_TABLE.update({
    "aierr.bad_base": ("AI 接口地址不对 (只支持 http/https 地址): {u}",
                       "Invalid AI base URL (only http/https supported): {u}"),
    "aierr.empty_value": ("(空)", "(empty)"),
    "aierr.public_http": ("公网地址只支持 https (http 会明文发送 API Key): {u}",
                          "Public URLs must use https (http sends the API key in plaintext): {u}"),
    "aierr.need_base": ("请先填写接口地址", "Enter the base URL first"),
    "aierr.models_too_large": ("模型列表响应过大", "Model list response too large"),
    "aierr.fetch_models_fail": ("获取模型列表失败 (HTTP {code}): {detail}",
                               "Failed to fetch model list (HTTP {code}): {detail}"),
    "aierr.cannot_connect_models": ("无法连接模型服务: {reason}",
                                    "Cannot connect to model service: {reason}"),
    "aierr.need_key": ("还没填 AI 接口的 API Key：到「设置」的「AI 模型中心」选服务、填 key 即可。",
                      "No API key set: open Settings → AI Model Center, choose a provider and enter its key."),
    "aierr.incomplete": ("AI 设置里的接口地址/模型名没填完整，先到「设置」补上。",
                        "Base URL or model name is incomplete. Fill it in under Settings."),
    "aierr.stream_line_too_large": ("AI 流式响应单行超过 1 MiB，已中止",
                                   "A single streaming line exceeded 1 MiB; aborted"),
    "aierr.response_too_large": ("AI 响应超过 2 MiB，已中止",
                                 "AI response exceeded 2 MiB; aborted"),
    "aierr.http": ("AI 接口返回 {code} 错误。{detail}",
                   "AI API returned error {code}. {detail}"),
    "aierr.conn": ("AI 接口连不上 ({detail})，检查网络后重试。",
                   "Cannot connect to the AI API ({detail}); check your network and retry."),
    "aierr.bad_format": ("AI 接口返回的格式看不懂，换个模型或检查接口地址。",
                        "Unrecognized AI response format; try another model or check the base URL."),
})

# 附件读取
_TABLE.update({
    "att.read_fail": ("文件读不了 (只支持文本文件)",
                      "Cannot read the file (only text files supported)"),
    "att.too_large": ("文件超过 12MB，请拆分后再附加",
                      "File exceeds 12 MB; split it before attaching"),
    "att.unsupported": ("暂不支持这种格式，请转成 .docx/.xlsx/.pdf 或文本后再试",
                       "This format is not supported; convert to .docx/.xlsx/.pdf or text first"),
    "att.bomb": ("文件解压后体积远超正常范围 (疑似异常文件)，已中止解析",
                "Decompressed size is far beyond the normal range (suspect file); parsing aborted"),
    "att.no_text": ("没能从文件里提取到文字 (扫描版 PDF 请截图后用图片提问)",
                   "No text could be extracted (for scanned PDFs, take a screenshot and ask with the image)"),
})

# 网络层
_TABLE.update({
    "net.redirect": ("接口要求跳转到其他地址，为保护密钥已中止",
                    "The API requested a redirect to another address; aborted to protect the key"),
})

# 翻译引擎错误码
_TABLE.update({
    "trerr.baidu": ("百度翻译错误 {code}: {msg}",
                   "Baidu Translate error {code}: {msg}"),
    "trerr.youdao": ("有道翻译错误码 {code}",
                    "Youdao Translate error code {code}"),
    "trerr.google": ("谷歌翻译错误 {code}: {msg}",
                    "Google Translate error {code}: {msg}"),
})

# 更新检查
_TABLE.update({
    "upd.unreachable": ("无法连接更新服务器：开启代理或配置更新镜像后重试，或到发布页手动下载",
                       "Cannot reach the update server: enable a proxy or configure an update mirror, or download manually from the releases page"),
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
