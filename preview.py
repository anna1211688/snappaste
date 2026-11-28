# -*- coding: utf-8 -*-
"""组件库视觉预览 (开发期使用)。"""
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QFrame,
)

from kivo.ui.theme import Theme
from kivo.ui.components import (
    PrimaryButton, SecondaryButton, DangerButton, GhostButton,
    SectionHeader, MutedLabel, Switch, SearchInput, NavItem,
    EmptyState, MessageActionBar,
)


def build(theme: Theme) -> QWidget:
    root = QWidget()
    root.setObjectName("root")
    outer = QHBoxLayout(root)
    outer.setContentsMargins(16, 16, 16, 16)
    outer.setSpacing(14)

    # 侧栏
    side = QFrame()
    side.setObjectName("sidebar")
    side.setFixedWidth(200)
    sl = QVBoxLayout(side)
    sl.setContentsMargins(10, 14, 10, 14)
    sl.setSpacing(6)
    for i, (k, ic, lb) in enumerate([
        ("copy", "copy", "剪贴板"), ("ai", "ai", "AI 助手"), ("translate", "translate", "翻译"),
        ("phrases", "phrases", "常用语"), ("project", "project", "项目"), ("voice", "voice", "语音"),
        ("fx", "fx", "汇率"), ("clock", "clock", "世界时钟"), ("calc", "calc", "计算器"),
        ("download", "download", "下载"), ("gear", "gear", "设置"),
    ]):
        item = NavItem(k, ic, lb)
        if i == 1:
            item.setChecked(True)
        sl.addWidget(item)
    sl.addStretch()
    outer.addWidget(side)

    # 内容滚动区
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    card = QFrame()
    card.setObjectName("card")
    cl = QVBoxLayout(card)
    cl.setContentsMargins(24, 22, 24, 24)
    cl.setSpacing(14)

    cl.addWidget(SectionHeader("按钮"))
    row = QHBoxLayout()
    row.setSpacing(10)
    for b in (PrimaryButton("主按钮", icon_name="copy"),
              SecondaryButton("次按钮", icon_name="gear"),
              DangerButton("危险", icon_name="close"),
              GhostButton("幽灵")):
        row.addWidget(b)
    row.addStretch()
    cl.addLayout(row)

    cl.addWidget(SectionHeader("开关 / 辅助文字"))
    row = QHBoxLayout()
    row.setSpacing(10)
    sw = Switch(True)
    sw._on_color = theme.c("success")
    sw._off_color = theme.c("border_strong")
    row.addWidget(sw)
    row.addWidget(MutedLabel("这是一段弱化说明文字"))
    row.addStretch()
    cl.addLayout(row)

    cl.addWidget(SectionHeader("搜索"))
    cl.addWidget(SearchInput("搜索剪贴板 / 对话"))

    cl.addWidget(SectionHeader("AI 回复操作栏"))
    bar = MessageActionBar()
    bar.action_triggered.connect(lambda key: print("action:", key))
    cl.addWidget(bar)

    cl.addWidget(SectionHeader("空状态"))
    cl.addWidget(EmptyState("folder-open", "暂无内容", "这里还没有任何记录",
                            action_text="立即新建", on_action=lambda: None))

    cl.addStretch()
    scroll.setWidget(card)
    outer.addWidget(scroll, 1)
    return root


def main():
    app = QApplication(sys.argv)
    theme = Theme(dark=False)
    app.setStyleSheet(theme.base_qss())
    w = build(theme)
    w.resize(1080, 820)
    if "--shot" in sys.argv:
        out = sys.argv[sys.argv.index("--shot") + 1]
        app.processEvents()
        w.grab().save(out)
        print("saved", out)
        return
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
