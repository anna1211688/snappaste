# -*- coding: utf-8 -*-
"""软件自检面板: 六项检测结果，后台线程执行。"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton
from ...core.selfcheck import CHK_ITEMS


class _Worker(QObject):
    finished = Signal(dict)

    def __init__(self, runner):
        super().__init__()
        self.runner = runner

    def run(self):
        self.finished.emit(self.runner.run())


class SelfCheckPanel(QWidget):
    def __init__(self, theme: Theme, runner):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.runner = runner
        self._thread = None
        self._rows = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        title = QLabel("软件自检")
        title.setObjectName("hero")
        outer.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=16, alpha=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(8)

        for key, label in CHK_ITEMS:
            row = QHBoxLayout()
            name = QLabel(label)
            name.setFixedWidth(140)
            result = QLabel("待检测")
            result.setObjectName("chkWait")
            row.addWidget(name)
            row.addWidget(result)
            row.addStretch()
            lay.addLayout(row)
            self._rows[key] = result

        run_btn = PrimaryButton("开始自检", icon_name="zap")
        run_btn.clicked.connect(self.run_check)
        btn_row = QHBoxLayout()
        btn_row.addStretch(); btn_row.addWidget(run_btn)
        lay.addLayout(btn_row)
        outer.addWidget(card)
        outer.addStretch()

    def run_check(self):
        if self._thread is not None:
            return
        for lab in self._rows.values():
            lab.setText("检测中…")
            lab.setObjectName("chkWait")
            lab.style().unpolish(lab); lab.style().polish(lab)

        self._thread = QThread(self)
        self._worker = _Worker(self.runner)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

    def _on_finished(self, results):
        for key, (ok, extra) in results.items():
            lab = self._rows[key]
            text = ("正常" if ok else "异常") + (f" — {extra}" if extra else "")
            lab.setText(text)
            lab.setObjectName("chkOk" if ok else "chkBad")
            lab.style().unpolish(lab); lab.style().polish(lab)
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
