# -*- coding: utf-8 -*-
"""应用组装层: 创建并连接核心服务与 UI 面板 (composition root)。"""
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
from .ui.panels.ai_panel import AIPanel
from .ui.panels.voice_panel import VoicePanel
from .ui.panels.trans_panel import TranslatePanel
from .ui.panels.clip_panel import ClipPanel
from .ui.panels.phrase_panel import PhrasePanel
from .ui.panels.project_panel import ProjectPanel
from .ui.panels.fx_panel import FxPanel
from .ui.panels.clock_panel import ClockPanel
from .ui.panels.calc_panel import CalcPanel
from .ui.panels.download_panel import DownloadPanel
from .ui.panels.pomo_panel import PomoPanel
from .ui.panels.winman_panel import WinmanPanel


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

    def pane_factory(self, key):
        if key == "ai":
            return AIPanel(self._theme, self.ai_client, self.chat_store)
        if key == "voice":
            return VoicePanel(self._theme, self.voice_client, self.ai_client)
        if key == "trans":
            return TranslatePanel(self._theme, self.translate_client, self.ai_client)
        if key == "clip":
            return ClipPanel(self._theme, self.clip_store)
        if key == "phrases":
            return PhrasePanel(self._theme, self.phrase_store)
        if key == "project":
            return ProjectPanel(self._theme, self.project_store)
        if key == "fx":
            return FxPanel(self._theme, self.fx_store)
        if key == "clock":
            return ClockPanel(self._theme, self.clock_store)
        if key == "calc":
            return CalcPanel(self._theme, self.calc_store)
        if key == "dl":
            return DownloadPanel(self._theme, self.download_store)
        if key == "pomo":
            return PomoPanel(self._theme, self.pomo_store)
        if key == "winman":
            return WinmanPanel(self._theme, self.window_manager)
        return None

    def make_main_services(self, theme):
        self._theme = theme
        return {"pane_factory": self.pane_factory,
                "settings_factory": lambda: None}
