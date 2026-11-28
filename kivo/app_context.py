# -*- coding: utf-8 -*-
"""应用组装层: 创建并连接核心服务与 UI 面板 (composition root)。

面板类一律在 pane_factory 内首次使用时才导入, 避免启动时一次性加载全部
面板模块, 配合 MainWindow 的懒加载加快启动。
"""
from __future__ import annotations

from .core.config import ConfigManager
from .core.ai import AIClient
from .core.voice import VoiceClient
from .core.translate import TranslateClient
from .core.chat_store import ChatStore
from .core.clip_store import ClipStore
from .core.phrase_store import PhraseStore
from .core.project_store import ProjectStore
from .core.fx_store import FxStore
from .core.clock_store import ClockStore
from .core.calc_store import CalcStore
from .core.download_store import DownloadStore
from .core.pomo_store import PomoStore
from .core.winman import WindowManager
from .core.batch_store import BatchStore


class Services:
    def __init__(self):
        self.config = ConfigManager()
        self.ai_client = AIClient(self.config)
        self.voice_client = VoiceClient(self.config, self.ai_client)
        self.translate_client = TranslateClient(self.config)
        self.chat_store = ChatStore()
        self.clip_store = ClipStore()
        self.phrase_store = PhraseStore()
        self.project_store = ProjectStore()
        self.fx_store = FxStore()
        self.clock_store = ClockStore(self.config)
        self.calc_store = CalcStore()
        self.download_store = DownloadStore(self.config)
        self.pomo_store = PomoStore()
        self.window_manager = WindowManager()
        self.batch_store = BatchStore()

    def pane_factory(self, key):
        if key == "ai":
            from .ui.panels.ai_panel import AIPanel
            return AIPanel(self._theme, self.ai_client, self.chat_store)
        if key == "voice":
            from .ui.panels.voice_panel import VoicePanel
            return VoicePanel(self._theme, self.voice_client, self.ai_client)
        if key == "trans":
            from .ui.panels.trans_panel import TranslatePanel
            return TranslatePanel(self._theme, self.translate_client, self.ai_client)
        if key == "clip":
            from .ui.panels.clip_panel import ClipPanel
            return ClipPanel(self._theme, self.clip_store)
        if key == "phrases":
            from .ui.panels.phrase_panel import PhrasePanel
            return PhrasePanel(self._theme, self.phrase_store)
        if key == "project":
            from .ui.panels.project_panel import ProjectPanel
            return ProjectPanel(self._theme, self.project_store)
        if key == "fx":
            from .ui.panels.fx_panel import FxPanel
            return FxPanel(self._theme, self.fx_store)
        if key == "clock":
            from .ui.panels.clock_panel import ClockPanel
            return ClockPanel(self._theme, self.clock_store)
        if key == "calc":
            from .ui.panels.calc_panel import CalcPanel
            return CalcPanel(self._theme, self.calc_store)
        if key == "dl":
            from .ui.panels.download_panel import DownloadPanel
            return DownloadPanel(self._theme, self.download_store)
        if key == "pomo":
            from .ui.panels.pomo_panel import PomoPanel
            return PomoPanel(self._theme, self.pomo_store)
        if key == "winman":
            from .ui.panels.winman_panel import WinmanPanel
            return WinmanPanel(self._theme, self.window_manager)
        if key == "batch":
            from .ui.panels.batch_panel import BatchPanel
            return BatchPanel(self._theme, self.batch_store)
        if key == "dev":
            from .ui.panels.dev_panel import DevPanel
            return DevPanel(self._theme)
        return None

    def make_main_services(self, theme):
        self._theme = theme

        def _settings():
            from .ui.panels.settings_panel import SettingsPanel
            return SettingsPanel(theme, self.config)

        return {"pane_factory": self.pane_factory,
                "settings_factory": _settings}
