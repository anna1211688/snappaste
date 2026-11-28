# -*- coding: utf-8 -*-
"""应用组装层: 创建并连接核心服务与 UI 面板 (composition root)。"""
from __future__ import annotations

from .core.config import ConfigManager
from .core.ai import AIClient
from .core.chat_store import ChatStore
from .ui.panels.ai_panel import AIPanel


class Services:
    def __init__(self):
        self.config = ConfigManager()
        self.ai_client = AIClient(self.config)
        self.chat_store = ChatStore()

    def pane_factory(self, key):
        if key == "ai":
            return AIPanel(self._theme, self.ai_client, self.chat_store)
        return None

    def make_main_services(self, theme):
        self._theme = theme
        return {"pane_factory": self.pane_factory,
                "settings_factory": lambda: None}
