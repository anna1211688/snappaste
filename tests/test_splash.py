# -*- coding: utf-8 -*-
"""启动屏测试。"""
from PySide6.QtWidgets import QSplashScreen

from kivo.ui.theme import Theme
from kivo.ui.splash import create_splash, set_message


def test_create_splash(qapp):
    s = create_splash(Theme(False))
    assert isinstance(s, QSplashScreen)
    assert not s.pixmap().isNull()


def test_set_message_updates(qapp):
    s = create_splash(Theme(False))
    set_message(s, Theme(False), "正在加载模块…")
    assert not s.pixmap().isNull()
    # 更新后仍可正常显示
    s.show()
    qapp.processEvents()
    assert s.isVisible()
    s.close()


def test_finish_on_window(qapp):
    from PySide6.QtWidgets import QWidget
    s = create_splash(Theme(False))
    host = QWidget()
    s.show()
    qapp.processEvents()
    # finish 会在目标窗口出现后关闭启动屏, 不抛异常
    s.finish(host)
    host.show()
    qapp.processEvents()
