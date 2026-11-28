# -*- coding: utf-8 -*-
"""KIVO (PySide6) 应用入口。

运行: python3 app.py
无显示环境截图: QT_QPA_PLATFORM=offscreen python3 app.py --shot out.png [--pane ai]
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from kivo.ui.theme import Theme
from kivo.ui.main_window import MainWindow
from kivo.ui.splash import create_splash, set_message
from kivo.app_context import Services
from kivo.core import i18n, data


def main() -> int:
    app = QApplication(sys.argv)
    theme = Theme(dark=False)
    app.setStyleSheet(theme.base_qss())

    is_shot = "--shot" in sys.argv
    splash = None
    if not is_shot:
        splash = create_splash(theme)
        splash.show()
        app.processEvents()

    if splash is not None:
        set_message(splash, theme, i18n.tr("splash.loading"))
        app.processEvents()
    services = Services()
    i18n.configure(services.config)

    # 生产环境开启异步写盘: 主线程只做内存序列化, 磁盘 I/O 交给后台线程
    data.set_async(True)

    def _on_quit():
        # 退出前确保所有排队数据落盘, 再停止后台写线程
        data.flush_all()
        data.shutdown_async()

    app.aboutToQuit.connect(_on_quit)

    win = MainWindow(theme, services.make_main_services(theme))
    if "--pane" in sys.argv:
        i = sys.argv.index("--pane")
        win.select(sys.argv[i + 1])
    win.show()

    if splash is not None:
        splash.finish(win)

    if is_shot:
        i = sys.argv.index("--shot")
        out = sys.argv[i + 1] if i + 1 < len(sys.argv) else "shot.png"
        app.processEvents()
        win.grab().save(out)
        print("saved", out)
        return 0

    # 空闲时逐个预建面板, 后续切换即时呈现, 且不抢占首屏
    win.prewarm()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
