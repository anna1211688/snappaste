# -*- coding: utf-8 -*-
"""计算器面板: 显示屏 + 按键网格 + 计算历史。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QListWidget, QListWidgetItem,
)

from ..theme import Theme, add_shadow
from ..components import SectionHeader
from ...core.i18n import tr
from ...core.calc_store import CalcStore, ERROR


class CalcPanel(QWidget):
    def __init__(self, theme: Theme, calc_store: CalcStore | None = None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = calc_store or CalcStore()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.addStretch()

        wrap = QHBoxLayout()
        wrap.addStretch()
        wrap.addWidget(self._calc_card())
        wrap.addStretch()
        outer.addLayout(wrap)
        outer.addStretch()
        self._sync()

    def _calc_card(self):
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(380)
        add_shadow(card, blur=20, alpha=26)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)

        self.trail_lab = QLabel("")
        self.trail_lab.setObjectName("calcTrail")
        self.trail_lab.setAlignment(Qt.AlignRight)
        lay.addWidget(self.trail_lab)

        self.disp_lab = QLabel("0")
        self.disp_lab.setObjectName("calcDisplay")
        self.disp_lab.setAlignment(Qt.AlignRight)
        lay.addWidget(self.disp_lab)

        lay.addSpacing(6)
        grid = QGridLayout()
        grid.setSpacing(6)
        layout = [
            [("C", "calcDanger", self.store.clear), ("⌫", "calcOp", self.store.back),
             ("%", "calcOp", self.store.percent), ("÷", "calcOp", lambda: self.store.set_op("÷"))],
            [("7", "calcDigit", lambda: self.store.digit("7")), ("8", "calcDigit", lambda: self.store.digit("8")),
             ("9", "calcDigit", lambda: self.store.digit("9")), ("×", "calcOp", lambda: self.store.set_op("×"))],
            [("4", "calcDigit", lambda: self.store.digit("4")), ("5", "calcDigit", lambda: self.store.digit("5")),
             ("6", "calcDigit", lambda: self.store.digit("6")), ("−", "calcOp", lambda: self.store.set_op("-"))],
            [("1", "calcDigit", lambda: self.store.digit("1")), ("2", "calcDigit", lambda: self.store.digit("2")),
             ("3", "calcDigit", lambda: self.store.digit("3")), ("+", "calcOp", lambda: self.store.set_op("+"))],
            [("±", "calcOp", self.store.negate), ("0", "calcDigit", lambda: self.store.digit("0")),
             (".", "calcDigit", self.store.dot), ("=", "calcAccent", self.store.equals)],
        ]
        for r, row in enumerate(layout):
            for c, (txt, obj, cmd) in enumerate(row):
                b = QPushButton(txt)
                b.setObjectName(obj)
                b.setFixedSize(78, 52)
                b.clicked.connect(lambda _=False, fn=cmd: (fn(), self._sync()))
                grid.addWidget(b, r, c)
        lay.addLayout(grid)

        # 历史
        lay.addSpacing(8)
        hrow = QHBoxLayout()
        hrow.addWidget(SectionHeader(tr("calc.history")))
        hrow.addStretch()
        clear = QPushButton(tr("common.clear"))
        clear.setObjectName("calcClearHist")
        clear.clicked.connect(self._clear_history)
        hrow.addWidget(clear)
        lay.addLayout(hrow)

        self.hist_list = QListWidget()
        self.hist_list.setObjectName("calcHist")
        self.hist_list.setFixedHeight(130)
        self.hist_list.itemClicked.connect(self._pick_history)
        lay.addWidget(self.hist_list)
        self._fill_history()
        return card

    def _sync(self):
        shown = tr("common.error") if self.store.display == ERROR else self.store.display
        self.disp_lab.setText(shown)
        self.trail_lab.setText(self.store.trail)
        self._fill_history()

    def _fill_history(self):
        self.hist_list.clear()
        if not self.store.history:
            it = QListWidgetItem(tr("calc.empty"))
            it.setFlags(Qt.NoItemFlags)
            self.hist_list.addItem(it)
            return
        for h in self.store.history:
            self.hist_list.addItem(f"{h['e']} = {h['r']}")

    def _pick_history(self, item):
        idx = self.hist_list.row(item)
        if 0 <= idx < len(self.store.history):
            self.store.pick_history(idx)
            self._sync()

    def _clear_history(self):
        self.store.clear_history()
        self._sync()
