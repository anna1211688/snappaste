# -*- coding: utf-8 -*-
"""开发者工具箱面板: 时间戳/JSON/正则/Base64/单位换算五个标签页。"""
from __future__ import annotations

import time

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QCheckBox, QPlainTextEdit,
    QTabWidget, QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme
from ..components import SecondaryButton
from ..dialogs.base import show_toast
from ...core import devtools


class DevPanel(QWidget):
    def __init__(self, theme: Theme):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(10)

        title = QLabel("开发者工具箱")
        title.setObjectName("hero")
        outer.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._timestamp_tab(), "时间戳")
        tabs.addTab(self._json_tab(), "JSON")
        tabs.addTab(self._regex_tab(), "正则测试")
        tabs.addTab(self._b64_tab(), "Base64")
        tabs.addTab(self._unit_tab(), "单位换算")
        outer.addWidget(tabs, 1)

    # ---------- 时间戳 ----------
    def _timestamp_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        now = QLineEdit(str(int(time.time())))
        r1 = QHBoxLayout()
        r1.addWidget(now, 1)
        refresh = SecondaryButton("刷新")
        refresh.clicked.connect(lambda: now.setText(str(int(time.time()))))
        copy = SecondaryButton("复制")
        copy.clicked.connect(lambda: self._copy(now.text()))
        r1.addWidget(refresh); r1.addWidget(copy)
        lay.addLayout(r1)

        ts_in = QLineEdit(); ts_in.setPlaceholderText("输入时间戳")
        ts_out = QLabel("")
        r2 = QHBoxLayout()
        r2.addWidget(ts_in, 1)
        b2 = SecondaryButton("时间戳→日期")
        b2.clicked.connect(lambda: self._safe(
            lambda: ts_out.setText(devtools.ts_to_date(ts_in.text())),
            lambda: ts_out.setText("输入有误")))
        r2.addWidget(b2)
        lay.addLayout(r2)
        lay.addWidget(ts_out)

        d_in = QLineEdit(); d_in.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        d_out = QLabel("")
        r3 = QHBoxLayout()
        r3.addWidget(d_in, 1)
        b3 = SecondaryButton("日期→时间戳")
        b3.clicked.connect(lambda: self._safe(
            lambda: d_out.setText(str(devtools.date_to_ts(d_in.text()))),
            lambda: d_out.setText("输入有误")))
        r3.addWidget(b3)
        lay.addLayout(r3)
        lay.addWidget(d_out)
        lay.addStretch()
        return w

    # ---------- JSON ----------
    def _json_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        j_in = QPlainTextEdit(); j_in.setFixedHeight(120)
        j_out = QPlainTextEdit()
        row = QHBoxLayout()
        pretty = SecondaryButton("格式化")
        pretty.clicked.connect(lambda: self._safe(
            lambda: j_out.setPlainText(devtools.json_pretty(j_in.toPlainText())),
            lambda: j_out.setPlainText("JSON 解析失败")))
        minify = SecondaryButton("压缩")
        minify.clicked.connect(lambda: self._safe(
            lambda: j_out.setPlainText(devtools.json_minify(j_in.toPlainText())),
            lambda: j_out.setPlainText("JSON 解析失败")))
        row.addWidget(pretty); row.addWidget(minify); row.addStretch()
        lay.addWidget(j_in); lay.addLayout(row); lay.addWidget(j_out, 1)
        return w

    # ---------- 正则 ----------
    def _regex_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        r1 = QHBoxLayout()
        pat = QLineEdit(); pat.setPlaceholderText("正则表达式")
        ic = QCheckBox("ignore case")
        r1.addWidget(pat, 1); r1.addWidget(ic)
        lay.addLayout(r1)
        x_in = QPlainTextEdit(); x_in.setFixedHeight(110)
        lay.addWidget(x_in)
        out = QLabel("")
        out.setWordWrap(True)
        go = SecondaryButton("测试匹配")
        go.clicked.connect(lambda: self._safe(
            lambda: (lambda hits: out.setText(
                f"{len(hits)} 处匹配: " + " | ".join(hits[:20])))(
                devtools.regex_find(pat.text(), x_in.toPlainText(), ic.isChecked())),
            lambda: out.setText("正则表达式有误")))
        lay.addWidget(go); lay.addWidget(out); lay.addStretch()
        return w

    # ---------- Base64 ----------
    def _b64_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        b_in = QPlainTextEdit(); b_in.setFixedHeight(100)
        b_out = QPlainTextEdit(); b_out.setFixedHeight(100)
        row = QHBoxLayout()
        enc = SecondaryButton("编码")
        enc.clicked.connect(lambda: self._safe(
            lambda: b_out.setPlainText(devtools.b64_encode(b_in.toPlainText().strip())),
            lambda: b_out.setPlainText("编码失败")))
        dec = SecondaryButton("解码")
        dec.clicked.connect(lambda: self._safe(
            lambda: b_out.setPlainText(devtools.b64_decode(b_in.toPlainText().strip())),
            lambda: b_out.setPlainText("解码失败")))
        row.addWidget(enc); row.addWidget(dec); row.addStretch()
        lay.addWidget(b_in); lay.addLayout(row); lay.addWidget(b_out); lay.addStretch()
        return w

    # ---------- 单位换算 ----------
    def _unit_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        r1 = QHBoxLayout()
        cat = QComboBox()
        cat.addItems(list(devtools.UNIT_FACTORS))
        val = QLineEdit(); val.setFixedWidth(100); val.setText("1")
        frm = QComboBox(); to = QComboBox()
        out = QLabel("")

        def sync_units():
            units = list(devtools.UNIT_FACTORS[cat.currentText()])
            frm.clear(); frm.addItems(units)
            to.clear(); to.addItems(units)
            if len(units) > 1:
                to.setCurrentIndex(1)

        cat.currentTextChanged.connect(sync_units)
        sync_units()
        go = SecondaryButton("换算")
        go.clicked.connect(lambda: self._safe(
            lambda: out.setText(
                f"{devtools.unit_convert(val.text(), cat.currentText(), frm.currentText(), to.currentText()):g} {to.currentText()}"),
            lambda: out.setText("输入有误")))
        r1.addWidget(cat); r1.addWidget(val); r1.addWidget(frm)
        r1.addWidget(QLabel("→")); r1.addWidget(to); r1.addWidget(go)
        lay.addLayout(r1); lay.addWidget(out); lay.addStretch()
        return w

    # ---------- 工具 ----------
    def _safe(self, action, on_error):
        try:
            action()
        except (ValueError, KeyError, TypeError):
            on_error()

    def _copy(self, text):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
        show_toast(self, "已复制")
