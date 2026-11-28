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

        title = QLabel("设置")
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
        lay = self._section("通用")

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("语言"))
        self.lang = QComboBox()
        self.lang.addItems(["Chinese", "English"])
        self.lang.setCurrentText(self.config.get("Config", "Language", "Chinese"))
        self.lang.currentTextChanged.connect(self._on_lang)
        lang_row.addWidget(self.lang)
        lang_row.addWidget(MutedLabel("(重启后生效)"))
        lang_row.addStretch()
        lay.addLayout(lang_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("外观"))
        self.theme_group = QButtonGroup(self)
        cur_theme = self.config.get("Config", "Theme", "light")
        for txt, val in (("浅色", "light"), ("深色", "dark")):
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
        lay.addLayout(self._switch_row(self.wave, "提示音（复制/粘贴成功时响一声）"))

        entry_row = QHBoxLayout()
        entry_row.addStretch()
        ai_btn = SecondaryButton("AI 模型中心", icon_name="ai")
        ai_btn.clicked.connect(self._open_ai_settings)
        entry_row.addWidget(ai_btn)
        tr_btn = SecondaryButton("翻译服务", icon_name="translate")
        tr_btn.clicked.connect(self._open_translate_service)
        entry_row.addWidget(tr_btn)
        hk_btn = SecondaryButton("热键设置", icon_name="gear")
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
        lay = self._section("迷你窗口（复制/粘贴时自动悬浮）")
        row = QHBoxLayout()
        row.addWidget(QLabel("悬浮显示时间(秒, 0=不显示)"))
        self.mini_time = QLineEdit(self.config.get("Config", "MiniFormTime", "5"))
        self.mini_time.setFixedWidth(70)
        row.addWidget(self.mini_time)
        self.mini_always = Switch(self.config.get("Config", "MiniFormSet", "0") == "1")
        self.mini_always._on_color = self.theme.tokens["accent"]
        row.addWidget(self.mini_always)
        row.addWidget(MutedLabel("常显"))
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
        lay = self._section("剪贴板历史")
        self.clip_watch = Switch(False)
        self.clip_watch._on_color = self.theme.tokens["accent"]
        self.clip_watch.toggled.connect(self._on_clip_watch)
        lay.addLayout(self._switch_row(
            self.clip_watch, "自动记录复制的文字到剪贴板历史（自动去重，单条上限 20 万字，最多 2000 条）"))

    def _on_clip_watch(self, on):
        self.config.set("Config", "ClipWatch", "1" if on else "0")
        self._save()

    # ---------- 网络代理 ----------
    def _build_proxy(self):
        lay = self._section("网络代理")
        self.proxy_group = QButtonGroup(self)
        cur = self.config.get("Network", "ProxyMode", "system")
        pr = QHBoxLayout()
        for txt, val in (("跟随系统(推荐)", "system"), ("手动代理", "manual"),
                         ("直连(不使用代理)", "off")):
            rb = QRadioButton(txt)
            rb.setProperty("val", val)
            if val == cur:
                rb.setChecked(True)
            self.proxy_group.addButton(rb)
            pr.addWidget(rb)
        pr.addStretch()
        lay.addLayout(pr)

        ar = QHBoxLayout()
        ar.addWidget(QLabel("代理地址"))
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
        lay = self._section("更新镜像")
        row = QHBoxLayout()
        row.addWidget(QLabel("镜像地址"))
        self.mirror = QLineEdit(self.config.get("Network", "UpdateMirror", ""))
        row.addWidget(self.mirror, 1)
        save = QPushButton("保存")
        save.clicked.connect(self._save_mirror)
        row.addWidget(save)
        lay.addLayout(row)
        lay.addWidget(MutedLabel("留空 = 直连 GitHub；填写后优先走镜像，失败再回退。"))

    def _save_mirror(self):
        v = self.mirror.text().strip().rstrip("/")
        if v and not v.startswith(("http://", "https://")):
            show_toast(self, "请输入合法的 http(s) 地址")
            return
        self.config.set("Network", "UpdateMirror", v)
        self._save()
        show_toast(self, "更新镜像已保存")

    # ---------- 检查更新 ----------
    def _build_update(self):
        lay = self._section("检查更新")
        self.upd_status = QLabel("尚未检查")
        self.upd_status.setObjectName("updMuted")
        row = QHBoxLayout()
        check = PrimaryButton("检查更新", icon_name="refresh")
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
        self.upd_status.setText("正在检查更新…")
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
            self.upd_status.setText(err or "检查失败，请检查网络后重试")
            self.upd_status.setObjectName("updBad")
            self._restyle(self.upd_status)
            return
        tag, html_url = res[0], res[1]
        self._upd_html = html_url
        if is_newer(tag, VERSION):
            self.upd_status.setText(f"发现新版本：{tag}")
            self.upd_status.setObjectName("updGood")
            page = SecondaryButton("查看发布页", icon_name="browser")
            page.clicked.connect(self._open_release_page)
            self.upd_actions.addWidget(page)
        else:
            self.upd_status.setText("已是最新版本")
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
        lay = self._section("截图历史")
        row = QHBoxLayout()
        self.hist_save = Switch(self.config.get("Snip", "HistorySave", "1") == "1")
        self.hist_save._on_color = self.theme.tokens["accent"]
        row.addWidget(self.hist_save)
        row.addWidget(MutedLabel("保存历史截图"))
        row.addWidget(QLabel("最多保留"))
        self.hist_max = QLineEdit(self.config.get("Snip", "HistoryMax", "100"))
        self.hist_max.setFixedWidth(70)
        row.addWidget(self.hist_max)
        row.addWidget(QLabel("张"))
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
