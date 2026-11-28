# -*- coding: utf-8 -*-
"""系统设置面板测试。"""
import pytest

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.ui.theme import Theme
from kivo.ui.panels.settings_panel import SettingsPanel


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


@pytest.fixture
def sp(qapp):
    p = SettingsPanel(Theme(False), ConfigManager())
    p.show()
    qapp.processEvents()
    return p


def test_sections_count(sp):
    # 6 个分区卡片
    from PySide6.QtWidgets import QFrame
    cards = [w for w in sp.findChildren(QFrame) if w.objectName() == "card"]
    assert len(cards) == 6


def test_language_change(sp):
    sp.lang.setCurrentText("English")
    assert sp.config.get("Config", "Language") == "English"


def test_theme_radio(sp):
    dark = [b for b in sp.theme_group.buttons() if b.property("val") == "dark"][0]
    dark.setChecked(True)
    sp._on_theme(dark)
    assert sp.config.get("Config", "Theme") == "dark"


def test_wave_switch(sp):
    sp.wave.setChecked(True)
    assert sp.config.get("Config", "WaveSet") == "1"


def test_mini_save(sp):
    sp.mini_time.setText("10")
    sp.mini_always.setChecked(True)
    sp._save_mini()
    assert sp.config.get("Config", "MiniFormTime") == "10"
    assert sp.config.get("Config", "MiniFormSet") == "1"


def test_mini_ignores_bad_time(sp):
    sp.mini_time.setText("abc")
    sp._save_mini()
    # 非法值不覆盖原配置
    assert sp.config.get("Config", "MiniFormTime") == "5"


def test_proxy_save(sp):
    manual = [b for b in sp.proxy_group.buttons() if b.property("val") == "manual"][0]
    manual.setChecked(True)
    sp.proxy_server.setText("127.0.0.1:1080")
    sp._save_proxy()
    assert sp.config.get("Network", "ProxyMode") == "manual"
    assert sp.config.get("Network", "ProxyServer") == "127.0.0.1:1080"


def test_mirror_bad_address(sp):
    sp.mirror.setText("not-a-url")
    sp._save_mirror()
    # 非法地址不写入（fresh 配置无该键，返回 None）
    assert sp.config.get("Network", "UpdateMirror") is None


def test_mirror_good_address(sp):
    sp.mirror.setText("https://mirror.example.com/")
    sp._save_mirror()
    # 末尾斜杠被剥除
    assert sp.config.get("Network", "UpdateMirror") == "https://mirror.example.com"


def test_shots_save_clamp(sp):
    sp.hist_max.setText("999999")
    sp._save_shots()
    assert sp.config.get("Snip", "HistoryMax") == "9999"


def test_shots_save_default(sp):
    sp.hist_max.setText("bad")
    sp._save_shots()
    assert sp.config.get("Snip", "HistoryMax") == "100"
