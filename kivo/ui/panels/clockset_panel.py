# -*- coding: utf-8 -*-
"""世界时钟城市选择面板: 搜索、勾选(1–15)、确定写配置。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QLabel, QCheckBox, QScrollArea,
    QVBoxLayout, QHBoxLayout,
)

from ..theme import Theme
from ..components import PrimaryButton, SecondaryButton, SearchInput
from ...core import clock_store
from ...core.clock_store import MAX_CITIES


class ClockSetPanel(QWidget):
    def __init__(self, theme: Theme, config, on_done=None):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.config = config
        self.on_done = on_done
        self.selected = set(self._current_tz())
        self._checks = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(10)

        title = QLabel("选择世界时间城市")
        title.setObjectName("hero")
        outer.addWidget(title)

        hint = QLabel("勾选要显示的城市（本地永远在第一张）")
        hint.setObjectName("muted")
        outer.addWidget(hint)

        self.cnt = QLabel("")
        self.cnt.setObjectName("cntAccent")
        outer.addWidget(self.cnt)

        self.search = SearchInput("搜索城市，如 Tokyo、Sydney")
        self.search.textChanged.connect(self.render)
        outer.addWidget(self.search)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.body = QWidget()
        self.body.setObjectName("scrollBody")
        self.list_lay = QVBoxLayout(self.body)
        self.list_lay.setContentsMargins(4, 4, 4, 4)
        self.list_lay.setSpacing(2)
        self.scroll.setWidget(self.body)
        outer.addWidget(self.scroll)

        bar = QHBoxLayout()
        bar.addStretch()
        cancel = SecondaryButton("取消")
        cancel.clicked.connect(self._cancel)
        ok = PrimaryButton("确定")
        ok.clicked.connect(self.confirm)
        bar.addWidget(cancel); bar.addWidget(ok)
        outer.addLayout(bar)

        self.render()

    def _current_tz(self):
        raw = self.config.get("Config", "ClockCities", fallback="") or ""
        tz_list = [x.strip() for x in raw.split(",") if x.strip()]
        return tz_list or clock_store.CLOCK_DEFAULT

    def render(self):
        self._clear()
        rows = clock_store.search_cities(self.search.text())
        if not rows:
            miss = QLabel("没找到这个城市，换个关键词试试")
            miss.setObjectName("muted")
            self.list_lay.addWidget(miss)
        for name, tz, off in rows:
            cb = QCheckBox(f"{name}  ({off})" if off else f"{name}  ·  {tz}")
            cb.setObjectName("cityCheck")
            cb.setChecked(tz in self.selected)
            cb.toggled.connect(lambda checked, t=tz: self._toggle(t, checked))
            self.list_lay.addWidget(cb)
            self._checks[tz] = cb
        self.list_lay.addStretch()
        self._refresh_cnt()

    def _clear(self):
        while self.list_lay.count():
            item = self.list_lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None); w.deleteLater()
        self._checks = {}

    def _toggle(self, tz, checked):
        if checked:
            if len(self.selected) >= MAX_CITIES:
                # 超上限：回退勾选并提示
                cb = self._checks.get(tz)
                if cb is not None:
                    cb.blockSignals(True); cb.setChecked(False); cb.blockSignals(False)
                self._message(f"最多选 {MAX_CITIES} 个城市（本地不算）")
                return
            self.selected.add(tz)
        else:
            self.selected.discard(tz)
        self._refresh_cnt()

    def _refresh_cnt(self):
        self.cnt.setText(f"已选 {len(self.selected)} / {MAX_CITIES}")

    def _message(self, text):
        self.cnt.setText(text)

    def confirm(self):
        if not self.selected:
            self._message("至少选一个城市")
            return
        picked = clock_store.order_picked(self.selected)
        if not self.config.has_section("Config"):
            self.config.add_section("Config")
        self.config.set("Config", "ClockCities", ",".join(picked))
        self.config.save()
        if self.on_done:
            self.on_done(picked)

    def _cancel(self):
        if self.on_done:
            self.on_done(None)
