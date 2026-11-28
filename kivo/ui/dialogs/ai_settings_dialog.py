# -*- coding: utf-8 -*-
"""AI 模型中心弹窗: 服务商配置 / 模型列表 / 任务分配 / 连接测试四个标签页。"""
from __future__ import annotations

import threading

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QDialog, QFrame, QLabel, QLineEdit, QComboBox, QPushButton, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget, QListWidgetItem,
    QCheckBox,
)

from ..theme import Theme, add_shadow
from ..components import PrimaryButton, MutedLabel
from ..icons import icon
from .base import show_toast
from ...core.ai import AIClient, AI_PRESETS, provider_label
from ...core import ai_settings_store as astore
from ...core.i18n import tr


class _Signals(QObject):
    models = Signal(list)
    message = Signal(str)
    finished = Signal()


class AiSettingsDialog(QDialog):
    def __init__(self, parent, theme: Theme, config, ai_client=None):
        super().__init__(parent)
        self.theme = theme
        self.config = config
        self.client = ai_client or AIClient(config)
        self.profiles = astore.load_profiles(config)
        self._busy = False

        self.setObjectName("aiSetRoot")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(620)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        self.card = QFrame()
        self.card.setObjectName("aiSetCard")
        add_shadow(self.card, blur=30, dy=10, alpha=55)
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(18, 14, 18, 16)
        cl.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel(tr("ais.title"))
        title.setObjectName("title")
        head.addWidget(title); head.addStretch()
        close = QPushButton()
        close.setObjectName("iconBtn"); close.setFixedSize(30, 30)
        close.setCursor(Qt.PointingHandCursor)
        close.setIcon(icon("close"))
        close.clicked.connect(self.reject)
        head.addWidget(close)
        cl.addLayout(head)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("aiTabs")
        cl.addWidget(self.tabs)
        self._build_provider_tab()
        self._build_models_tab()
        self._build_routes_tab()
        self._build_test_tab()

        footer = QHBoxLayout()
        footer.addStretch()
        save = PrimaryButton(tr("ais.save_all"), icon_name="save")
        save.clicked.connect(self._save_all)
        footer.addWidget(save)
        cl.addLayout(footer)

        outer.addWidget(self.card)
        self.signals = _Signals()
        self.signals.models.connect(self._on_models_fetched)
        self.signals.message.connect(lambda m: self.test_result.setText(m))
        self.signals.finished.connect(lambda: setattr(self, "_busy", False))

    # ---------- 服务商配置 ----------
    def _build_provider_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        self._svc_key = self.client.cfg()["service"]
        self.svc_store = {k: self._read_svc(k) for k in AI_PRESETS}

        row = QHBoxLayout()
        row.addWidget(QLabel(tr("ais.provider")))
        self.svc = QComboBox()
        for k in AI_PRESETS:
            self.svc.addItem(provider_label(k), k)
        self.svc.setCurrentIndex(list(AI_PRESETS).index(self._svc_key))
        self.svc.currentIndexChanged.connect(self._on_svc_changed)
        row.addWidget(self.svc, 1)
        lay.addLayout(row)

        self.key_edit = QLineEdit(); self.key_edit.setEchoMode(QLineEdit.Password)
        self.base_edit = QLineEdit()
        self.model_edit = QLineEdit()
        grid = QGridLayout()
        grid.addWidget(QLabel("API Key"), 0, 0)
        grid.addWidget(self.key_edit, 0, 1)
        grid.addWidget(QLabel(tr("ais.base")), 1, 0)
        grid.addWidget(self.base_edit, 1, 1)
        grid.addWidget(QLabel(tr("ais.model")), 2, 0)
        grid.addWidget(self.model_edit, 2, 1)
        fetch = QPushButton(tr("ais.fetch"))
        fetch.setIcon(icon("refresh"))
        fetch.clicked.connect(self._fetch_models)
        grid.addWidget(fetch, 2, 2)
        add = QPushButton(tr("ais.add"))
        add.setIcon(icon("plus"))
        add.clicked.connect(self._add_current_model)
        grid.addWidget(add, 2, 3)
        lay.addLayout(grid)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(False)
        fetched_row = QHBoxLayout()
        fetched_row.addWidget(QLabel(tr("ais.available")))
        fetched_row.addWidget(self.model_combo, 1)
        use = QPushButton(tr("ais.use"))
        use.setIcon(icon("check"))
        use.clicked.connect(self._use_fetched_model)
        fetched_row.addWidget(use)
        lay.addLayout(fetched_row)

        lay.addWidget(MutedLabel(tr("ais.provider_hint")))
        lay.addStretch()
        self.tabs.addTab(tab, tr("ais.provider_tab"))
        self._load_svc_fields()

    def _read_svc(self, k):
        c = self.client.cfg(k)
        return [c["key"], c["model"], c["base"]]

    def _on_svc_changed(self):
        self._stash_svc(self._svc_key)
        self._svc_key = self.svc.currentData()
        self._load_svc_fields()

    def _stash_svc(self, k):
        self.svc_store[k] = [self.key_edit.text().strip(),
                             self.model_edit.text().strip(),
                             self.base_edit.text().strip()]

    def _load_svc_fields(self):
        key, model, base = self.svc_store[self._svc_key]
        self.key_edit.setText(key); self.model_edit.setText(model); self.base_edit.setText(base)

    def _current_svc_cfg(self):
        return {"service": self._svc_key,
                "key": self.key_edit.text().strip(),
                "model": self.model_edit.text().strip(),
                "base": self.base_edit.text().strip()}

    def _fetch_models(self):
        if self._busy:
            return
        self._busy = True
        cfg = self._current_svc_cfg()
        client = self.client
        signals = self.signals

        def work():
            try:
                ids = client.fetch_models(cfg)
                signals.models.emit(list(ids or []))
            except Exception as e:
                signals.message.emit(tr("ais.fetch_fail") + str(e))
            finally:
                signals.finished.emit()

        threading.Thread(target=work, daemon=True, name="kivo-ai-models").start()

    def _on_models_fetched(self, ids):
        self.model_combo.clear()
        self.model_combo.addItems(ids)
        if ids:
            show_toast(self, tr("ais.fetched_count", n=len(ids)))

    def _use_fetched_model(self):
        if self.model_combo.count():
            self.model_edit.setText(self.model_combo.currentText())

    def _add_current_model(self):
        model = self.model_edit.text().strip()
        if not model:
            show_toast(self, tr("ais.need_id"))
            return
        if astore.add_model(self.profiles, self._svc_key, model):
            self._refresh_model_list()
            show_toast(self, tr("ais.added") + model)
        else:
            show_toast(self, tr("ais.model_exists"))

    # ---------- 模型列表 ----------
    def _build_models_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        self.model_list = QListWidget()
        lay.addWidget(self.model_list)
        btns = QHBoxLayout()
        default = QPushButton(tr("ais.set_default"))
        default.setIcon(icon("star"))
        default.clicked.connect(self._set_selected_default)
        toggle = QPushButton(tr("ais.toggle"))
        toggle.clicked.connect(self._toggle_selected)
        delete = QPushButton(tr("ais.delete_model"))
        delete.setIcon(icon("trash"))
        delete.clicked.connect(self._delete_selected)
        for b in (default, toggle, delete):
            btns.addWidget(b)
        btns.addStretch()
        lay.addLayout(btns)
        self.tabs.addTab(tab, tr("ais.models_tab"))
        self._refresh_model_list()

    def _refresh_model_list(self):
        self.model_list.clear()
        for svc in AI_PRESETS:
            for p in self.profiles[svc]:
                state = tr("ais.enabled") if p["enabled"] else tr("ais.disabled")
                item = QListWidgetItem(
                    f"{provider_label(svc)} · {p['model']}（{state}）")
                item.setData(Qt.UserRole, (svc, p["model"]))
                self.model_list.addItem(item)

    def _selected_profile(self):
        item = self.model_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _set_selected_default(self):
        sel = self._selected_profile()
        if not sel:
            return
        svc, model = sel
        self.svc_store[svc][1] = model
        if svc == self._svc_key:
            self.model_edit.setText(model)
        show_toast(self, tr("ais.default_set"))

    def _toggle_selected(self):
        sel = self._selected_profile()
        if sel and astore.toggle_model(self.profiles, sel[0], sel[1]):
            self._refresh_model_list()

    def _delete_selected(self):
        sel = self._selected_profile()
        if sel and astore.remove_model(self.profiles, sel[0], sel[1]):
            self._refresh_model_list()

    # ---------- 任务分配 ----------
    def _build_routes_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.addWidget(MutedLabel(tr("ais.routes_hint")))
        self.route_combos = {}
        saved = astore.load_routes(self.config)
        names = [k for k in AI_PRESETS]
        for rk, label_key in astore.ROUTE_DEFS:
            row = QHBoxLayout()
            lab = QLabel(tr(label_key)); lab.setFixedWidth(90)
            row.addWidget(lab)
            combo = QComboBox()
            combo.addItem(tr("ais.follow"), ("", ""))
            for k in names:
                combo.addItem(provider_label(k), (k, ""))
            svc, model = saved[rk]
            if svc:
                idx = names.index(svc) + 1
                combo.setCurrentIndex(idx)
            row.addWidget(combo, 1)
            self.route_combos[rk] = combo
            lay.addLayout(row)
        lay.addStretch()
        self.tabs.addTab(tab, tr("ais.routes_tab"))

    # ---------- 连接测试 ----------
    def _build_test_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        self.fallback = QCheckBox(tr("ais.fallback"))
        self.fallback.setChecked(
            (self.config.get("AI", "AutoFallback", fallback="0") or "0").strip() == "1")
        lay.addWidget(self.fallback)
        self.test_result = QLabel(tr("ais.test_hint"))
        self.test_result.setWordWrap(True)
        self.test_result.setObjectName("aiTestResult")
        lay.addWidget(self.test_result)
        btn = QPushButton(tr("ais.test_provider"))
        btn.setIcon(icon("zap"))
        btn.clicked.connect(self._run_connection_test)
        lay.addWidget(btn)
        lay.addStretch()
        self.tabs.addTab(tab, tr("ais.test_tab"))

    def _run_connection_test(self):
        if self._busy:
            return
        self._busy = True
        self.test_result.setText(tr("ais.testing"))
        cfg = self._current_svc_cfg()
        client = self.client
        signals = self.signals

        def work():
            import time
            started = time.monotonic()
            try:
                r = client.chat_messages(
                    [{"role": "user", "content": "只回复两个字：正常"}],
                    cfg=cfg, max_tokens=16, timeout=30)
                elapsed = time.monotonic() - started
                reply = r if r else tr("ais.empty_reply")
                signals.message.emit(tr(
                    "ais.conn_ok", sec=f"{elapsed:.2f}", r=reply))
            except Exception as e:
                elapsed = time.monotonic() - started
                signals.message.emit(tr(
                    "ais.conn_fail", sec=f"{elapsed:.2f}", e=str(e)))
            finally:
                signals.finished.emit()

        threading.Thread(target=work, daemon=True, name="kivo-ai-test").start()

    # ---------- 统一保存 ----------
    def _save_all(self):
        self._stash_svc(self._svc_key)
        # 写各服务商的 Key/Model/Base
        for k, (key, model, base) in self.svc_store.items():
            pre = k.capitalize()
            self.config.set("AI", pre + "Key", key)
            self.config.set("AI", pre + "Model", model)
            self.config.set("AI", pre + "Base", base)
        self.config.set("AI", "Service", self._svc_key)
        astore.write_profiles(self.config, self.profiles)
        routes = {rk: combo.currentData() for rk, combo in self.route_combos.items()}
        astore.save_routes(self.config, routes)
        self.config.set("AI", "AutoFallback", "1" if self.fallback.isChecked() else "0")
        self.config.save()
        show_toast(self, tr("ais.saved"))
        self.accept()
