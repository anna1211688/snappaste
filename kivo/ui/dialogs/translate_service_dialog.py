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

TEST_SENTENCE = "Hello, nice to meet you."

# (key, 显示名)
SERVICES = [
    ("free", "免费接口（无需密钥）"),
    ("baidu", "百度翻译开放平台"),
    ("youdao", "有道翻译"),
    ("google", "谷歌翻译（Google Cloud）"),
]


class _Signals(QObject):
    message = Signal(str)
    finished = Signal()


class TranslateServiceDialog(Dialog):
    def __init__(self, parent, theme: Theme, config, client=None):
        super().__init__(parent, "翻译服务", width=480)
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
        for key, name in SERVICES:
            self.svc.addItem(name, key)
        idx = max(0, [k for k, _ in SERVICES].index(tc["service"]))
        self.svc.setCurrentIndex(idx)
        self._svc_key = tc["service"]
        self.svc.currentIndexChanged.connect(self._on_svc_changed)
        self._row("翻译服务", self.svc)

        self.app_id = QLineEdit()
        self._row("APP ID", self.app_id)

        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.Password)
        self._row("密钥", self.key)

        note = MutedLabel(
            "百度/有道到开放平台免费申请 APP ID 和密钥；谷歌只需填 API 密钥。"
            "密钥只存本机，没填或出错时自动用免费接口。")
        note.setWordWrap(True)
        self.body.addWidget(note)

        self.test_result = QLabel("")
        self.test_result.setObjectName("trTest")
        self.test_result.setWordWrap(True)
        self.body.addWidget(self.test_result)

        test = SecondaryButton("测试", icon_name="zap")
        test.clicked.connect(self._do_test)
        self.add_button(test)
        save = PrimaryButton("保存", icon_name="save")
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
        self.test_result.setText("测试中…")
        client = self.client
        signals = self.signals

        def work():
            try:
                if k == "baidu":
                    if not all(pair):
                        raise RuntimeError("先填 APP ID 和密钥")
                    r = client.baidu_translate(TEST_SENTENCE, "zh-CN", pair[0], pair[1])
                elif k == "youdao":
                    if not all(pair):
                        raise RuntimeError("先填 APP ID 和密钥")
                    r = client.youdao_translate(TEST_SENTENCE, "zh-CN", pair[0], pair[1])
                elif k == "google":
                    if not pair[1]:
                        raise RuntimeError("先填 API 密钥")
                    r = client.google_translate(TEST_SENTENCE, "zh-CN", pair[1])
                else:
                    r = client.translate_to(TEST_SENTENCE, "zh-CN")
                if r:
                    signals.message.emit(f"测试成功：{TEST_SENTENCE} → {r}")
                else:
                    signals.message.emit("测试失败：没拿到译文")
            except Exception as e:
                signals.message.emit(f"测试失败：{e}")
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
        show_toast(self, "翻译服务已保存")
        self.accept()
