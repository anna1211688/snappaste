# -*- coding: utf-8 -*-
"""组件库视觉预览 (开发期使用)。"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QFrame

from kivo.ui.theme import Theme, add_shadow
from kivo.ui.components import (
    Card, PrimaryButton, SecondaryButton, DangerButton, GhostButton, IconButton,
    IconBadge, SectionHeader, MutedLabel, Switch, Chip, SearchInput, ListRow,
    NavItem, ChatBubble, HLine,
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
    card = Card(shadow=True)
    cl = QVBoxLayout(card)
    cl.setContentsMargins(24, 22, 24, 24)
    cl.setSpacing(14)

    cl.addWidget(SectionHeader("按钮"))
    row = QHBoxLayout()
    row.setSpacing(10)
    for b in (PrimaryButton("主按钮"), SecondaryButton("次按钮"),
              DangerButton("危险"), GhostButton("幽灵"), IconButton("gear")):
        row.addWidget(b)
    row.addStretch()
    cl.addLayout(row)

    cl.addWidget(HLine())
    cl.addWidget(SectionHeader("图标底 / 开关 / 标签"))
    row = QHBoxLayout()
    row.setSpacing(10)
    for n in ("copy", "translate", "ai", "fx", "clock", "calc", "star"):
        row.addWidget(IconBadge(n))
    sw = Switch(True)
    sw._on_color = theme.c("success")
    sw._off_color = theme.c("border_strong")
    row.addWidget(sw)
    row.addWidget(Chip("标签一"))
    row.addWidget(Chip("标签二"))
    row.addStretch()
    cl.addLayout(row)

    cl.addWidget(HLine())
    cl.addWidget(SectionHeader("搜索"))
    cl.addWidget(SearchInput("搜索剪贴板 / 对话"))

    cl.addWidget(HLine())
    cl.addWidget(SectionHeader("列表行"))
    for n, t, s in [
        ("copy", "剪贴板记录", "2 分钟前 · 文本"),
        ("ai", "AI 对话", "昨天 · 关于方案的讨论"),
        ("translate", "翻译结果", "Hello → 你好"),
    ]:
        cl.addWidget(ListRow(n, t, s))

    cl.addWidget(HLine())
    cl.addWidget(SectionHeader("气泡"))
    bw = QWidget()
    bwl = QVBoxLayout(bw)
    bwl.setContentsMargins(0, 0, 0, 0)
    b1 = ChatBubble("帮我把这段文字翻译成英文", True)
    b2 = ChatBubble("好的，这是英文翻译结果。", False)
    bwl.addWidget(b1, 0, __import__("PySide6").QtCore.Qt.AlignRight)
    bwl.addWidget(b2, 0, __import__("PySide6").QtCore.Qt.AlignLeft)
    cl.addWidget(bw)

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
