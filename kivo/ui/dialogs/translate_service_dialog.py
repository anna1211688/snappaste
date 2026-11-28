# -*- coding: utf-8 -*-
"""翻译服务设置弹窗: 四家服务选择、凭证录入、连通性测试与保存。"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QComboBox

from ..theme import Theme
from ..components import PrimaryButton, SecondaryButton, MutedLabel
from .base import Dialog, show_toast
from ...core.translate import TranslateClient
from ...core.i18n import tr

TEST_SENTENCE = "Hello, nice to meet you."

# (key, i18n key)
SERVICES = [
    ("free", "ts.free"),
    ("baidu", "ts.baidu"),
    ("youdao", "ts.youdao"),
    ("google", "ts.google"),
]


class _Signals(QObject):
    message = Signal(str)
    finished = Signal()


class TranslateServiceDialog(Dialog):
    def __init__(self, parent, theme: Theme, config, client=None):
        super().__init__(parent, tr("ts.title"), width=480)
        self.theme = theme
        self.config = config
        self.client = client or TranslateClient(config)
        tc = self.client.trans_cfg()
        self.creds = {
            "baidu": [tc["baidu_id"], tc["baidu_key"]],
            "youdao": [tc["youdao_id"], tc["youdao_secret"]],
            "google": ["", tc["google_key"]],
        }
        self._busy = False

        self.svc = QComboBox()
        for key, name_key in SERVICES:
            self.svc.addItem(tr(name_key), key)
        idx = max(0, [k for k, _ in SERVICES].index(tc["service"]))
        self.svc.setCurrentIndex(idx)
        self._svc_key = tc["service"]
        self.svc.currentIndexChanged.connect(self._on_svc_changed)
        self._row(tr("ts.title"), self.svc)

        self.app_id = QLineEdit()
        self._row(tr("ts.app_id"), self.app_id)

        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.Password)
        self._row(tr("ts.secret"), self.key)

        note = MutedLabel(tr("ts.note"))
        note.setWordWrap(True)
        self.body.addWidget(note)

        self.test_result = QLabel("")
        self.test_result.setObjectName("trTest")
        self.test_result.setWordWrap(True)
        self.body.addWidget(self.test_result)

        test = SecondaryButton(tr("ts.test_btn"), icon_name="zap")
        test.clicked.connect(self._do_test)
        self.add_button(test)
        save = PrimaryButton(tr("common.save"), icon_name="save")
        save.clicked.connect(self._do_save)
        self.add_button(save)

        self.signals = _Signals()
        self.signals.message.connect(self.test_result.setText)
        self.signals.finished.connect(lambda: setattr(self, "_busy", False))
        self._load_fields()

    def _row(self, label, widget):
        from PySide6.QtWidgets import QHBoxLayout
        row = QHBoxLayout()
        lab = QLabel(label)
        lab.setFixedWidth(70)
        row.addWidget(lab)
        row.addWidget(widget, 1)
        self.body.addLayout(row)

    @property
    def service_key(self):
        return self.svc.currentData()

    def _on_svc_changed(self):
        # 信号触发时 combo 已指向新值，先按记录的旧 key 收走当前输入
        self._collect(self._svc_key)
        self._svc_key = self.service_key
        self._load_fields()

    def _collect_current(self):
        self._collect(self._svc_key)

    def _collect(self, k):
        if k in self.creds:
            self.creds[k] = [self.app_id.text().strip(), self.key.text().strip()]

    def _load_fields(self):
        k = self.service_key
        if k == "free":
            self.app_id.setText(""); self.key.setText("")
            self.app_id.setEnabled(False); self.key.setEnabled(False)
        elif k == "google":
            self.app_id.setText(""); self.key.setText(self.creds["google"][1])
            self.app_id.setEnabled(False); self.key.setEnabled(True)
        else:
            pair = self.creds[k]
            self.app_id.setText(pair[0]); self.key.setText(pair[1])
            self.app_id.setEnabled(True); self.key.setEnabled(True)

    def _do_test(self):
        if self._busy:
            return
        self._collect_current()
        k = self.service_key
        pair = self.creds.get(k, ["", ""])
        self._busy = True
        self.test_result.setText(tr("ts.testing"))
        client = self.client
        signals = self.signals

        def work():
            try:
                if k == "baidu":
                    if not all(pair):
                        raise RuntimeError(tr("ts.need_creds"))
                    r = client.baidu_translate(TEST_SENTENCE, "zh-CN", pair[0], pair[1])
                elif k == "youdao":
                    if not all(pair):
                        raise RuntimeError(tr("ts.need_creds"))
                    r = client.youdao_translate(TEST_SENTENCE, "zh-CN", pair[0], pair[1])
                elif k == "google":
                    if not pair[1]:
                        raise RuntimeError(tr("ts.need_google"))
                    r = client.google_translate(TEST_SENTENCE, "zh-CN", pair[1])
                else:
                    r = client.translate_to(TEST_SENTENCE, "zh-CN")
                if r:
                    signals.message.emit(
                        tr("ts.test_ok") + f"{TEST_SENTENCE} → {r}")
                else:
                    signals.message.emit(tr("ts.test_fail_empty"))
            except Exception as e:
                signals.message.emit(tr("ts.test_fail") + str(e))
            finally:
                signals.finished.emit()

        threading.Thread(target=work, daemon=True, name="kivo-tr-test").start()

    def _do_save(self):
        self._collect_current()
        self.config.set("Translate", "Service", self.service_key)
        self.config.set("Translate", "BaiduAppId", self.creds["baidu"][0])
        self.config.set("Translate", "BaiduKey", self.creds["baidu"][1])
        self.config.set("Translate", "YoudaoAppId", self.creds["youdao"][0])
        self.config.set("Translate", "YoudaoSecret", self.creds["youdao"][1])
        self.config.set("Translate", "GoogleKey", self.creds["google"][1])
        self.config.save()
        show_toast(self, tr("ts.saved"))
        self.accept()
