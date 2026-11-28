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
from kivo.app_context import Services


def main() -> int:
    app = QApplication(sys.argv)
    theme = Theme(dark=False)
    app.setStyleSheet(theme.base_qss())

    services = Services()
    win = MainWindow(theme, services.make_main_services(theme))
    if "--pane" in sys.argv:
        i = sys.argv.index("--pane")
        key = sys.argv[i + 1]
        win.select(key)
    win.show()

    if "--shot" in sys.argv:
        i = sys.argv.index("--shot")
        out = sys.argv[i + 1] if i + 1 < len(sys.argv) else "shot.png"
        app.processEvents()
        win.grab().save(out)
        print("saved", out)
        return 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
