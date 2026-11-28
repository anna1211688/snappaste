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
from .ui.panels.ai_panel import AIPanel
from .ui.panels.voice_panel import VoicePanel
from .ui.panels.trans_panel import TranslatePanel
from .ui.panels.clip_panel import ClipPanel
from .ui.panels.phrase_panel import PhrasePanel


class Services:
    def __init__(self):
        self.config = ConfigManager()
        self.ai_client = AIClient(self.config)
        self.voice_client = VoiceClient(self.config, self.ai_client)
        self.translate_client = TranslateClient(self.config)
        self.chat_store = ChatStore()
        self.clip_store = ClipStore()
        self.phrase_store = PhraseStore()

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
        return None

    def make_main_services(self, theme):
        self._theme = theme
        return {"pane_factory": self.pane_factory,
                "settings_factory": lambda: None}
