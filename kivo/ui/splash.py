# -*- coding: utf-8 -*-
"""轻量启动屏: 全部用 QPainter 程序化绘制, 不依赖外部图片资源。"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QSplashScreen

from ..core.i18n import tr
from ..core.paths import APP_NAME, VERSION

_WIDTH, _HEIGHT = 380, 240


def _draw(theme: "object", message: str) -> QPixmap:
    pm = QPixmap(_WIDTH, _HEIGHT)
    pm.fill(QColor(theme.c("surface")))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # 顶部强调色装饰条
    p.fillRect(0, 0, _WIDTH, 6, QColor(theme.c("accent")))

    name_font = QFont()
    name_font.setPointSize(22)
    name_font.setBold(True)
    p.setFont(name_font)
    p.setPen(QColor(theme.c("text")))
    p.drawText(40, 100, APP_NAME)

    sub_font = QFont()
    sub_font.setPointSize(11)
    p.setFont(sub_font)
    p.setPen(QColor(theme.c("muted")))
    p.drawText(40, 130, f"v{VERSION}")

    p.drawText(40, 198, message)
    p.end()
    return pm


def create_splash(theme) -> QSplashScreen:
    """创建并返回启动屏 (调用方负责 show 与 finish)。"""
    return QSplashScreen(_draw(theme, tr("splash.loading")))


def set_message(splash: QSplashScreen, theme, text: str):
    """更新启动屏加载文案并立即重绘。"""
    splash.setPixmap(_draw(theme, text))
    splash.repaint()
