# -*- coding: utf-8 -*-
"""弹窗视觉预览。"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

from kivo.ui.theme import Theme
from kivo.ui.dialogs.base import Dialog, show_toast
from kivo.ui.components import PrimaryButton, SecondaryButton, Switch, MutedLabel


class SampleDialog(Dialog):
    def __init__(self, parent):
        super().__init__(parent, "示例弹窗", width=420)
        self.body.addWidget(MutedLabel("这是一个圆角无边框弹窗, 带柔和阴影与淡入动画。"))
        sw = Switch(True)
        sw._on_color = "#34C759"
        sw._off_color = "#D1D1D6"
        self.body.addWidget(sw)
        self.add_button(SecondaryButton("取消"))
        self.add_button(PrimaryButton("确定"), accept=True)


def main():
    app = QApplication(sys.argv)
    theme = Theme(dark=False)
    app.setStyleSheet(theme.base_qss())
    host = QWidget()
    host.setObjectName("root")
    host.resize(900, 640)
    lay = QVBoxLayout(host)
    lay.addWidget(QPushButton("宿主窗口"))
    host.show()

    if "--shot" in sys.argv:
        dlg = SampleDialog(host)
        dlg.show()
        app.processEvents()
        out = sys.argv[sys.argv.index("--shot") + 1]
        dlg.grab().save(out)
        print("saved", out)
        return
    dlg = SampleDialog(host)
    dlg.exec()
    show_toast(host, "操作已完成")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
