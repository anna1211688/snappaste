# -*- coding: utf-8 -*-
"""系统设置面板测试。"""
import pytest
from PySide6.QtWidgets import QPushButton

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
    # 7 个分区卡片
    from PySide6.QtWidgets import QFrame
    cards = [w for w in sp.findChildren(QFrame) if w.objectName() == "card"]
    assert len(cards) == 7


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


class _FakeClient:
    def __init__(self, result=None, raise_msg=None):
        self._result = result
        self._raise = raise_msg

    def fetch_latest_release(self):
        if self._raise:
            raise RuntimeError(self._raise)
        return self._result


def _wait_idle(qapp, sp, tries=100):
    for _ in range(tries):
        qapp.processEvents()
        if not sp._upd_busy:
            return
        import time
        time.sleep(0.01)
    qapp.processEvents()


def test_update_new_version(qapp):
    client = _FakeClient(("v9.9.9", "https://example.com/r", "", "", ""))
    p = SettingsPanel(Theme(False), ConfigManager(), update_client=client)
    p._check_update()
    _wait_idle(qapp, p)
    assert "发现新版本" in p.upd_status.text()
    assert p.upd_status.objectName() == "updGood"
    btns = [b for b in p.findChildren(QPushButton) if b.text() == "查看发布页"]
    assert btns


def test_update_latest(qapp):
    client = _FakeClient(("v0.0.1", "https://example.com/r", "", "", ""))
    p = SettingsPanel(Theme(False), ConfigManager(), update_client=client)
    p._check_update()
    _wait_idle(qapp, p)
    assert "已是最新版本" in p.upd_status.text()


def test_update_fail(qapp):
    client = _FakeClient(raise_msg="网络不通")
    p = SettingsPanel(Theme(False), ConfigManager(), update_client=client)
    p._check_update()
    _wait_idle(qapp, p)
    assert p.upd_status.objectName() == "updBad"
    assert "网络不通" in p.upd_status.text()


def test_update_busy_guard(qapp):
    client = _FakeClient(("v9.9.9", "u", "", "", ""))
    p = SettingsPanel(Theme(False), ConfigManager(), update_client=client)
    p._upd_busy = True
    p._check_update()  # 忙碌时直接返回，不抛错
    assert p.upd_status.text() == "尚未检查"
