# -*- coding: utf-8 -*-
"""世界时钟面板: 城市卡片网格(每秒刷新) + 跨时区时间换算。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout,
    QGridLayout, QScrollArea,
)

from ..theme import Theme, add_shadow
from ..components import (
    PrimaryButton, SecondaryButton, SectionHeader, MutedLabel,
)
from ...core.clock_store import (
    make_tz, city_label, weekday_label,
)
from ...core.i18n import tr


class ClockPanel(QWidget):
    def __init__(self, theme: Theme, clock_store):
        super().__init__()
        self.setObjectName("panelRoot")
        self.theme = theme
        self.store = clock_store
        self._cards = []  # (tz, time_label, date_label, dot_label)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel(tr("clock.title"))
        title.setObjectName("hero")
        head.addWidget(title)
        head.addStretch()
        edit = SecondaryButton(tr("clock.edit"), icon_name="edit")
        edit.clicked.connect(self.edit_cities)
        head.addWidget(edit)
        outer.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_host = QWidget()
        self.grid = QGridLayout(grid_host)
        self.grid.setContentsMargins(2, 2, 2, 2)
        self.grid.setSpacing(10)
        scroll.setWidget(grid_host)
        outer.addWidget(scroll, 1)

        outer.addWidget(self._convert_card())
        self.build_cards()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()

    # ---------- 城市卡片 ----------
    def build_cards(self):
        self._clear_grid()
        self._cards = []
        # 本地第一
        entries = [(tr("clock.local"), None, 0)] + self.store.selected()
        for idx, (name, tzname, stdh) in enumerate(entries):
            tz = None if tzname is None else make_tz(tzname, stdh)
            card = self._city_card(name, tz, idx == 0, tzname)
            r, c = divmod(idx, 4)
            self.grid.addWidget(card, r, c)

    def _clear_grid(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget():
                w = it.widget()
                w.setParent(None)
                w.deleteLater()

    def _city_card(self, name, tz, is_local, tzname=None):
        card = QFrame()
        card.setObjectName("card")
        add_shadow(card, blur=16, alpha=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)

        top = QHBoxLayout()
        if is_local:
            display = tr("clock.local")
        else:
            display = city_label(tzname, name)
        nm = QLabel(display)
        nm.setObjectName("cityName" if not is_local else "localName")
        dot = QLabel("●")
        dot.setObjectName("dayDot")
        top.addWidget(nm)
        top.addStretch()
        top.addWidget(dot)
        lay.addLayout(top)

        time_lab = QLabel("--:--:--")
        time_lab.setObjectName("clockTime")
        date_lab = QLabel("")
        date_lab.setObjectName("mutedLabel")
        lay.addWidget(time_lab)
        lay.addWidget(date_lab)
        self._cards.append((tz, time_lab, date_lab, dot))
        return card

    def tick(self):
        for tz, time_lab, date_lab, dot in self._cards:
            now = datetime.now() if tz is None else self.store.now_in(tz)
            time_lab.setText(now.strftime("%H:%M:%S"))
            wd = weekday_label(now.weekday())
            date_lab.setText(f"{now.strftime('%Y-%m-%d')}  {wd}")
            day = (6 <= now.hour < 19) if tz is None else self.store.is_day(tz)
            dot.setStyleSheet("color:%s; background:transparent"
                              % ("#F5A623" if day else "#5B6B82"))

    # ---------- 时间换算 ----------
    def _convert_card(self):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        lay.addWidget(SectionHeader(tr("clock.convert_head")))

        row = QHBoxLayout()
        row.addWidget(QLabel(tr("clock.peer_city")))
        self.city_cb = QComboBox()
        self._tz_list = []
        for name, tzname, stdh in self.store.selected():
            self.city_cb.addItem(city_label(tzname, name))
            self._tz_list.append(make_tz(tzname, stdh))
        row.addWidget(self.city_cb)
        row.addSpacing(10)
        row.addWidget(QLabel(tr("clock.my_time")))
        self.my_time = QLineEdit(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.my_time.setFixedWidth(150)
        row.addWidget(self.my_time)
        go = PrimaryButton(tr("clock.convert"), icon_name="check")
        go.clicked.connect(self.do_convert)
        row.addWidget(go)
        row.addStretch()
        lay.addLayout(row)

        self.result_lab = MutedLabel("")
        lay.addWidget(self.result_lab)
        return card

    def do_convert(self):
        if not self._tz_list:
            return
        try:
            local_dt = datetime.strptime(self.my_time.text().strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            self.result_lab.setText(tr("clock.time_fmt"))
            return
        tz = self._tz_list[self.city_cb.currentIndex()]
        target = self.store.convert(local_dt, tz)
        self.result_lab.setText(
            tr("clock.peer_local") + target.strftime("%Y-%m-%d %H:%M") + "  "
            + weekday_label(target.weekday()))

    def edit_cities(self):
        # 城市选择面板在设置/独立面板实现；此处保留入口
        self.result_lab.setText(tr("clock.edit_entry"))
