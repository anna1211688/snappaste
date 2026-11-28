# -*- coding: utf-8 -*-
"""系统设置面板: 可滚动分区卡片，改完即存。"""
from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QLineEdit, QComboBox, QRadioButton, QButtonGroup,
    QPushButton, QVBoxLayout, QHBoxLayout, QScrollArea,
)

from ..theme import Theme, add_shadow
from ..components import (
    Switch, SectionHeader, MutedLabel, PrimaryButton, SecondaryButton,
)
from ..dialogs.base import show_toast
from ...core.update import UpdateClient, is_newer
from ...core.paths import VERSION
from ...core.i18n import tr


class _UpdEvent(QEvent):
    def __init__(self, res, err=None):
        super().__init__(QEvent.User)
        self.res = res
        self.err = err


class SettingsPanel(QWidget):
    def __init__(self, theme: Theme, config, update_client=None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.config = config
        self.update_client = update_client or UpdateClient(config)
        self._upd_busy = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(10)

        title = QLabel(tr("common.settings"))
        title.setObjectName("hero")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        host.setObjectName("transparentPane")
        self.body = QVBoxLayout(host)
        self.body.setContentsMargins(2, 2, 6, 2)
        self.body.setSpacing(12)
        scroll.setWidget(host)
        outer.addWidget(scroll, 1)

        self._build_general()
        self._build_mini()
        self._build_clipwatch()
        self._build_proxy()
        self._build_mirror()
        self._build_update()
        self._build_shots()
        self.body.addStretch()

    # ---------- 辅助 ----------
    def _section(self, title):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=14, alpha=20)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        lay.addWidget(SectionHeader(title))
        self.body.addWidget(card)
        return lay

    def _switch_row(self, sw, text):
        row = QHBoxLayout()
        row.addWidget(sw)
        row.addWidget(MutedLabel(text))
        row.addStretch()
        return row

    def _save(self):
        self.config.save()

    # ---------- 通用 ----------
    def _build_general(self):
        lay = self._section(tr("set.general"))

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(tr("set.language")))
        self.lang = QComboBox()
        self.lang.addItems(["Chinese", "English"])
        self.lang.setCurrentText(self.config.get("Config", "Language", "Chinese"))
        self.lang.currentTextChanged.connect(self._on_lang)
        lang_row.addWidget(self.lang)
        lang_row.addWidget(MutedLabel(tr("set.restart")))
        lang_row.addStretch()
        lay.addLayout(lang_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel(tr("set.appearance")))
        self.theme_group = QButtonGroup(self)
        cur_theme = self.config.get("Config", "Theme", "light")
        for txt, val in ((tr("set.light"), "light"), (tr("set.dark"), "dark")):
            rb = QRadioButton(txt)
            rb.setProperty("val", val)
            if val == cur_theme:
                rb.setChecked(True)
            self.theme_group.addButton(rb)
            theme_row.addWidget(rb)
        self.theme_group.buttonClicked.connect(self._on_theme)
        theme_row.addStretch()
        lay.addLayout(theme_row)

        self.wave = Switch(self.config.get("Config", "WaveSet", "0") == "1")
        self.wave._on_color = self.theme.tokens["accent"]
        self.wave.toggled.connect(self._on_wave)
        lay.addLayout(self._switch_row(self.wave, tr("set.wave")))

        entry_row = QHBoxLayout()
        entry_row.addStretch()
        ai_btn = SecondaryButton(tr("set.ai_center"), icon_name="ai")
        ai_btn.clicked.connect(self._open_ai_settings)
        entry_row.addWidget(ai_btn)
        tr_btn = SecondaryButton(tr("set.trans_service"), icon_name="translate")
        tr_btn.clicked.connect(self._open_translate_service)
        entry_row.addWidget(tr_btn)
        hk_btn = SecondaryButton(tr("set.hotkey"), icon_name="gear")
        hk_btn.clicked.connect(self._open_hotkey)
        entry_row.addWidget(hk_btn)
        lay.addLayout(entry_row)

    def _open_ai_settings(self):
        from ..dialogs.ai_settings_dialog import AiSettingsDialog
        dlg = AiSettingsDialog(self, self.theme, self.config)
        dlg.exec()
        dlg.deleteLater()

    def _open_hotkey(self):
        from ..dialogs.hotkey_dialog import HotkeyDialog
        dlg = HotkeyDialog(self, self.theme, self.config)
        dlg.exec()
        dlg.deleteLater()

    def _open_translate_service(self):
        from ..dialogs.translate_service_dialog import TranslateServiceDialog
        dlg = TranslateServiceDialog(self, self.theme, self.config)
        dlg.exec()
        dlg.deleteLater()

    def _on_lang(self, val):
        self.config.set("Config", "Language", val)
        self._save()

    def _on_theme(self, btn):
        self.config.set("Config", "Theme", btn.property("val"))
        self._save()

    def _on_wave(self, on):
        self.config.set("Config", "WaveSet", "1" if on else "0")
        self._save()

    # ---------- 迷你窗口 ----------
    def _build_mini(self):
        lay = self._section(tr("set.mini"))
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("set.mini_time")))
        self.mini_time = QLineEdit(self.config.get("Config", "MiniFormTime", "5"))
        self.mini_time.setFixedWidth(70)
        row.addWidget(self.mini_time)
        self.mini_always = Switch(self.config.get("Config", "MiniFormSet", "0") == "1")
        self.mini_always._on_color = self.theme.tokens["accent"]
        row.addWidget(self.mini_always)
        row.addWidget(MutedLabel(tr("set.always")))
        row.addStretch()
        lay.addLayout(row)
        self.mini_time.editingFinished.connect(self._save_mini)
        self.mini_always.toggled.connect(self._save_mini)

    def _save_mini(self):
        t = self.mini_time.text().strip()
        if t.isdigit():
            self.config.set("Config", "MiniFormTime", t)
        self.config.set("Config", "MiniFormSet",
                        "1" if self.mini_always.isChecked() else "0")
        self._save()

    # ---------- 剪贴板历史 ----------
    def _build_clipwatch(self):
        lay = self._section(tr("set.clip_history"))
        self.clip_watch = Switch(False)
        self.clip_watch._on_color = self.theme.tokens["accent"]
        self.clip_watch.toggled.connect(self._on_clip_watch)
        lay.addLayout(self._switch_row(
            self.clip_watch, tr("set.clip_watch")))

    def _on_clip_watch(self, on):
        self.config.set("Config", "ClipWatch", "1" if on else "0")
        self._save()

    # ---------- 网络代理 ----------
    def _build_proxy(self):
        lay = self._section(tr("set.proxy"))
        self.proxy_group = QButtonGroup(self)
        cur = self.config.get("Network", "ProxyMode", "system")
        pr = QHBoxLayout()
        for txt, val in ((tr("set.follow_system"), "system"),
                         (tr("set.manual"), "manual"),
                         (tr("set.direct"), "off")):
            rb = QRadioButton(txt)
            rb.setProperty("val", val)
            if val == cur:
                rb.setChecked(True)
            self.proxy_group.addButton(rb)
            pr.addWidget(rb)
        pr.addStretch()
        lay.addLayout(pr)

        ar = QHBoxLayout()
        ar.addWidget(QLabel(tr("set.proxy_addr")))
        self.proxy_server = QLineEdit(self.config.get("Network", "ProxyServer", ""))
        self.proxy_server.setPlaceholderText("127.0.0.1:7890")
        ar.addWidget(self.proxy_server, 1)
        lay.addLayout(ar)
        self.proxy_group.buttonClicked.connect(self._save_proxy)
        self.proxy_server.editingFinished.connect(self._save_proxy)

    def _save_proxy(self):
        btn = self.proxy_group.checkedButton()
        self.config.set("Network", "ProxyMode",
                        btn.property("val") if btn else "system")
        self.config.set("Network", "ProxyServer", self.proxy_server.text().strip())
        self._save()

    # ---------- 更新镜像 ----------
    def _build_mirror(self):
        lay = self._section(tr("set.mirror"))
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("set.mirror_addr")))
        self.mirror = QLineEdit(self.config.get("Network", "UpdateMirror", ""))
        row.addWidget(self.mirror, 1)
        save = QPushButton(tr("common.save"))
        save.clicked.connect(self._save_mirror)
        row.addWidget(save)
        lay.addLayout(row)
        lay.addWidget(MutedLabel(tr("set.mirror_hint")))

    def _save_mirror(self):
        v = self.mirror.text().strip().rstrip("/")
        if v and not v.startswith(("http://", "https://")):
            show_toast(self, tr("set.bad_url"))
            return
        self.config.set("Network", "UpdateMirror", v)
        self._save()
        show_toast(self, tr("set.mirror_saved"))

    # ---------- 检查更新 ----------
    def _build_update(self):
        lay = self._section(tr("set.check_update"))
        self.upd_status = QLabel(tr("set.not_checked"))
        self.upd_status.setObjectName("updMuted")
        row = QHBoxLayout()
        check = PrimaryButton(tr("set.check_update"), icon_name="refresh")
        check.clicked.connect(self._check_update)
        row.addWidget(check)
        row.addWidget(self.upd_status)
        row.addStretch()
        lay.addLayout(row)

        self.upd_actions = QHBoxLayout()
        self.upd_actions.addStretch()
        lay.addLayout(self.upd_actions)

    def _check_update(self):
        if self._upd_busy:
            return
        self._upd_busy = True
        self.upd_status.setText(tr("set.checking"))
        client = self.update_client

        def work():
            try:
                res = client.fetch_latest_release()
                self._on_upd_done(res)
            except Exception as e:
                self._on_upd_fail(str(e))

        import threading
        threading.Thread(target=work, daemon=True, name="kivo-update").start()

    def _on_upd_done(self, res):
        from PySide6.QtWidgets import QApplication
        QApplication.instance().postEvent(self, _UpdEvent(res))

    def _on_upd_fail(self, msg):
        from PySide6.QtWidgets import QApplication
        QApplication.instance().postEvent(self, _UpdEvent(None, msg))

    def _apply_upd_result(self, res, err):
        self._upd_busy = False
        self._clear_upd_actions()
        if err:
            self.upd_status.setText(err or tr("set.check_fail"))
            self.upd_status.setObjectName("updBad")
            self._restyle(self.upd_status)
            return
        tag, html_url = res[0], res[1]
        self._upd_html = html_url
        if is_newer(tag, VERSION):
            self.upd_status.setText(tr("set.new_version") + tag)
            self.upd_status.setObjectName("updGood")
            page = SecondaryButton(tr("set.view_page"), icon_name="browser")
            page.clicked.connect(self._open_release_page)
            self.upd_actions.addWidget(page)
        else:
            self.upd_status.setText(tr("set.up_to_date"))
            self.upd_status.setObjectName("updMuted")
        self._restyle(self.upd_status)

    def _clear_upd_actions(self):
        while self.upd_actions.count():
            it = self.upd_actions.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None); w.deleteLater()
        self.upd_actions.addStretch()

    def _open_release_page(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(getattr(self, "_upd_html", "")))

    @staticmethod
    def _restyle(w):
        w.style().unpolish(w); w.style().polish(w)

    def customEvent(self, event):
        if isinstance(event, _UpdEvent):
            self._apply_upd_result(event.res, event.err)
        else:
            super().customEvent(event)

    # ---------- 截图历史 ----------
    def _build_shots(self):
        lay = self._section(tr("set.shot_history"))
        row = QHBoxLayout()
        self.hist_save = Switch(self.config.get("Snip", "HistorySave", "1") == "1")
        self.hist_save._on_color = self.theme.tokens["accent"]
        row.addWidget(self.hist_save)
        row.addWidget(MutedLabel(tr("set.save_shots")))
        row.addWidget(QLabel(tr("set.keep_max")))
        self.hist_max = QLineEdit(self.config.get("Snip", "HistoryMax", "100"))
        self.hist_max.setFixedWidth(70)
        row.addWidget(self.hist_max)
        row.addWidget(QLabel(tr("set.zhang")))
        row.addStretch()
        lay.addLayout(row)
        self.hist_save.toggled.connect(self._save_shots)
        self.hist_max.editingFinished.connect(self._save_shots)

    def _save_shots(self):
        t = self.hist_max.text().strip()
        keep = int(t) if t.isdigit() else 100
        keep = min(9999, max(1, keep))
        self.config.set("Snip", "HistorySave",
                        "1" if self.hist_save.isChecked() else "0")
        self.config.set("Snip", "HistoryMax", str(keep))
        self._save()
