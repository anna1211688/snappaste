# -*- coding: utf-8 -*-
"""AI 模型中心弹窗测试。"""
import time

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.core.ai import AI_PRESETS
from kivo.ui.theme import Theme
from kivo.ui.dialogs.ai_settings_dialog import AiSettingsDialog


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


class FakeAIClient:
    def __init__(self, models=None, chat_reply="正常", fail=None):
        self._models = models or []
        self._reply = chat_reply
        self.fail = fail

    def cfg(self, svc=None):
        svc = svc or "zhipu"
        name, base, model = AI_PRESETS[svc]
        return {"service": svc, "key": "test-key", "model": model, "base": base}

    def fetch_models(self, cfg, timeout=15):
        if self.fail:
            raise RuntimeError(self.fail)
        return self._models

    def chat_messages(self, messages, cfg=None, max_tokens=16, timeout=30):
        if self.fail:
            raise RuntimeError(self.fail)
        return self._reply


def _wait(qapp, cond, tries=400):
    for _ in range(tries):
        qapp.processEvents()
        if cond():
            return True
        time.sleep(0.01)
    qapp.processEvents()
    return cond()


@pytest.fixture
def parent(qapp):
    w = QWidget(); w.show(); qapp.processEvents()
    return w


@pytest.fixture
def dlg(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient())
    d.show(); qapp.processEvents()
    return d


def test_four_tabs(dlg):
    assert dlg.tabs.count() == 4


def test_svc_switch_keeps_fields(dlg):
    dlg.svc.setCurrentIndex(0)  # zhipu
    dlg.key_edit.setText("zhipu-key")
    dlg.svc.setCurrentIndex(1)  # bailian
    dlg.svc.setCurrentIndex(0)  # back
    assert dlg.key_edit.text() == "zhipu-key"


def test_fetch_models_fills_combo(qapp, parent):
    client = FakeAIClient(models=["m1", "m2"])
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), client)
    d._fetch_models()
    assert _wait(qapp, lambda: d.model_combo.count() == 2)
    assert _wait(qapp, lambda: d._busy is False)


def test_fetch_models_failure(qapp, parent):
    client = FakeAIClient(fail="boom")
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), client)
    d._fetch_models()
    assert _wait(qapp, lambda: "获取失败" in d.test_result.text())


def test_use_fetched_model(qapp, parent):
    client = FakeAIClient(models=["model-x"])
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), client)
    d._fetch_models()
    _wait(qapp, lambda: d.model_combo.count() == 1)
    d._use_fetched_model()
    assert d.model_edit.text() == "model-x"


def test_add_current_model(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient())
    d.model_edit.setText("my-model")
    d._add_current_model()
    qapp.processEvents()
    assert d.profiles[d._svc_key][0]["model"] == "my-model"
    assert d.model_list.count() >= 1


def test_add_empty_model_ignored(dlg):
    dlg.model_edit.setText("")
    dlg._add_current_model()
    assert dlg.model_list.count() == 0


def test_toggle_selected(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient())
    d.model_edit.setText("m"); d._add_current_model()
    d.model_list.setCurrentRow(0)
    d._toggle_selected()
    svc, model = d.model_list.item(0).data(Qt.UserRole)
    assert d.profiles[svc][0]["enabled"] is False


def test_delete_selected(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient())
    d.model_edit.setText("m"); d._add_current_model()
    d.model_list.setCurrentRow(0)
    d._delete_selected()
    assert d.model_list.count() == 0


def test_set_default(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient())
    d.model_edit.setText("def-model"); d._add_current_model()
    d.model_list.setCurrentRow(0)
    d._set_selected_default()
    assert d.svc_store[d._svc_key][1] == "def-model"


def test_route_combo_switch(dlg):
    combo = dlg.route_combos["RouteChat"]
    assert combo.currentData() == ("", "")
    combo.setCurrentIndex(1)
    assert combo.currentData()[0] == list(AI_PRESETS)[0]


def test_connection_test_success(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient())
    d._run_connection_test()
    assert _wait(qapp, lambda: "连接正常" in d.test_result.text())
    assert _wait(qapp, lambda: d._busy is False)


def test_connection_test_failure(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient(fail="x"))
    d._run_connection_test()
    assert _wait(qapp, lambda: "连接失败" in d.test_result.text())


def test_busy_guard(dlg):
    dlg._busy = True
    dlg._fetch_models()
    assert dlg.model_combo.count() == 0


def test_save_all_writes(qapp, parent):
    d = AiSettingsDialog(parent, Theme(False), ConfigManager(), FakeAIClient())
    d.model_edit.setText("saved-model"); d._add_current_model()
    d.route_combos["RouteChat"].setCurrentIndex(1)
    d._save_all()
    qapp.processEvents()
    assert d.config.get("AI", "Service") == d._svc_key
    assert d.config.get("AI", "AutoFallback") == "0"
    # 模型档案已落配置
    assert "saved-model" in d.config.get("AI", "ModelProfiles")
