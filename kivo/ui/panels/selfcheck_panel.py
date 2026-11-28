# -*- coding: utf-8 -*-
"""软件自检面板: 六项检测结果，后台线程执行。"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton
from ...core.i18n import tr
from ...core.selfcheck import CHK_ITEMS


class _Worker(QObject):
    finished = Signal(dict)

    def __init__(self, runner):
        super().__init__()
        self.runner = runner

    def run(self):
        # 兜底: 任何检查项抛异常都归为失败, 确保 finished 一定发出, 线程能正常退出
        try:
            results = self.runner.run()
        except Exception as e:
            results = {key: (False, str(e)[:80]) for key, _ in CHK_ITEMS}
        self.finished.emit(results)


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

        title = QLabel(tr("chk.title"))
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
            name = QLabel(tr(label))
            name.setFixedWidth(140)
            result = QLabel(tr("chk.wait"))
            result.setObjectName("chkWait")
            row.addWidget(name)
            row.addWidget(result)
            row.addStretch()
            lay.addLayout(row)
            self._rows[key] = result

        run_btn = PrimaryButton(tr("chk.start"), icon_name="zap")
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
            lab.setText(tr("chk.running"))
            lab.setObjectName("chkWait")
            lab.style().unpolish(lab); lab.style().polish(lab)

        # 线程不挂 parent: 避免面板销毁时强删仍在运行的线程
        self._thread = QThread()
        self._worker = _Worker(self.runner)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

    def _on_finished(self, results):
        for key, (ok, extra) in results.items():
            lab = self._rows[key]
            text = (tr("chk.ok") if ok else tr("chk.bad")) + (f" — {extra}" if extra else "")
            lab.setText(text)
            lab.setObjectName("chkOk" if ok else "chkBad")
            lab.style().unpolish(lab); lab.style().polish(lab)
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
