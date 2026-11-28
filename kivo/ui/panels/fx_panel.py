# -*- coding: utf-8 -*-
"""汇率换算面板: 货币换算卡 + 基准汇率表，后台获取每日汇率。"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
)

from ..theme import Theme, add_shadow
from ..components import SecondaryButton, SectionHeader, MutedLabel
from ...core.fx_store import FX_CURRENCIES


class _Signals(QObject):
    ok = Signal()
    failed = Signal(str)


class FxPanel(QWidget):
    def __init__(self, theme: Theme, fx_store):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.fx = fx_store
        self.loading = False

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel("汇率换算")
        title.setObjectName("hero")
        self.updated_label = MutedLabel("")
        refresh = SecondaryButton("刷新")
        refresh.clicked.connect(self.reload)
        head.addWidget(title)
        head.addWidget(self.updated_label)
        head.addStretch()
        head.addWidget(refresh)
        root.addLayout(head)

        root.addWidget(self._convert_card())
        root.addWidget(self._table_card(), 1)

        self.status = MutedLabel("正在获取最新汇率…")
        root.addWidget(self.status)

        self.signals = _Signals()
        self.signals.ok.connect(self._after_fetch)
        self.signals.failed.connect(self._fetch_failed)
        self.reload()

    def _currency_combo(self):
        cb = QComboBox()
        for code, name in FX_CURRENCIES:
            cb.addItem(f"{code} {name}", code)
        return cb

    def _convert_card(self):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=22, alpha=28)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        lay.addWidget(SectionHeader("货币换算"))

        row = QHBoxLayout()
        self.amount = QLineEdit("100")
        self.amount.setFixedWidth(110)
        self.from_cb = self._currency_combo()
        self.from_cb.setCurrentIndex(1)  # CNY
        swap = QPushButton("⇄")
        swap.setObjectName("iconBtn")
        swap.setFixedWidth(34)
        swap.clicked.connect(self._swap)
        self.to_cb = self._currency_combo()  # USD
        self.result = QLabel("")
        self.result.setObjectName("fxResult")
        row.addWidget(self.amount)
        row.addWidget(self.from_cb)
        row.addWidget(swap)
        row.addWidget(self.to_cb)
        row.addWidget(self.result, 1)
        lay.addLayout(row)

        self.hint = MutedLabel("")
        lay.addWidget(self.hint)
        for w in (self.amount, self.from_cb, self.to_cb):
            if isinstance(w, QComboBox):
                w.currentIndexChanged.connect(self._convert)
        self.amount.textChanged.connect(self._convert)
        return card

    def _table_card(self):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=18, alpha=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(SectionHeader("各币种汇率"))
        top.addStretch()
        top.addWidget(QLabel("基准"))
        self.base_cb = self._currency_combo()  # USD
        self.base_cb.currentIndexChanged.connect(self._fill_table)
        top.addWidget(self.base_cb)
        lay.addLayout(top)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["货币", "代码", "汇率"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        lay.addWidget(self.table)
        return card

    # ---------- 交互 ----------
    def _swap(self):
        a, b = self.from_cb.currentIndex(), self.to_cb.currentIndex()
        self.from_cb.setCurrentIndex(b)
        self.to_cb.setCurrentIndex(a)

    def _convert(self):
        try:
            amt = float(self.amount.text().strip())
        except (ValueError, AttributeError):
            self.result.setText("")
            self.hint.setText("金额填数字")
            return
        fr, to = self.from_cb.currentData(), self.to_cb.currentData()
        res = self.fx.convert(amt, fr, to)
        if res is None:
            return
        self.result.setText(f"= {res:,.2f} {to}")
        unit = self.fx.table_rate(fr, to)
        if unit is not None:
            self.hint.setText(f"1 {fr} = {self.fx.fmt(unit)} {to}")

    def _fill_table(self):
        base = self.base_cb.currentData()
        self.table.setRowCount(0)
        if not self.fx.rates:
            return
        for i, (code, name) in enumerate(FX_CURRENCIES):
            r = self.fx.table_rate(base, code)
            if r is None:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(code))
            self.table.setItem(row, 2, QTableWidgetItem(self.fx.fmt(r)))
            if row % 2:
                for c in range(3):
                    self.table.item(row, c).setBackground(QColor(self.theme.tokens["soft"]))

    def reload(self):
        if self.loading:
            return
        self.loading = True
        self.status.setText("正在获取最新汇率…")
        signals = self.signals

        def work():
            try:
                self.fx.fetch()
                signals.ok.emit()
            except Exception as e:
                signals.failed.emit(str(e))

        threading.Thread(target=work, daemon=True, name="kivo-fx").start()

    def _after_fetch(self):
        self.loading = False
        self.updated_label.setText("更新时间：" + self.fx.updated)
        self.status.setText("数据来源：open.er-api.com（免费接口，每日更新）")
        self._fill_table()
        self._convert()

    def _fetch_failed(self, msg):
        self.loading = False
        self.status.setText("汇率获取失败：" + msg)
