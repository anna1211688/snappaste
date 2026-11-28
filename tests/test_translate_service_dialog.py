# -*- coding: utf-8 -*-
"""翻译服务设置弹窗测试。"""
import time

import pytest
from PySide6.QtWidgets import QWidget

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.ui.theme import Theme
from kivo.ui.dialogs.translate_service_dialog import (
    TranslateServiceDialog, TEST_SENTENCE,
)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


class FakeClient:
    def __init__(self, result="你好", fail=None):
        self.result = result
        self.fail = fail
        self.calls = []

    def trans_cfg(self):
        return {"service": "free", "baidu_id": "", "baidu_key": "",
                "youdao_id": "", "youdao_secret": "", "google_key": ""}

    def _maybe(self, name, *args):
        self.calls.append((name,) + args)
        if self.fail:
            raise RuntimeError(self.fail)
        return self.result

    def baidu_translate(self, q, t, appid, key):
        return self._maybe("baidu", q, t, appid, key)

    def youdao_translate(self, q, t, appid, key):
        return self._maybe("youdao", q, t, appid, key)

    def google_translate(self, q, t, key):
        return self._maybe("google", q, t, key)

    def translate_to(self, q, t):
        return self._maybe("free", q, t)


def _wait(qapp, cond, tries=200):
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
    d = TranslateServiceDialog(parent, Theme(False), ConfigManager(), FakeClient())
    d.show(); qapp.processEvents()
    return d


def test_free_disables_inputs(dlg):
    assert dlg.service_key == "free"
    assert not dlg.app_id.isEnabled()
    assert not dlg.key.isEnabled()


def test_switch_to_baidu_enables(dlg):
    dlg.svc.setCurrentIndex(1)
    assert dlg.service_key == "baidu"
    assert dlg.app_id.isEnabled() and dlg.key.isEnabled()


def test_switch_to_google_appid_disabled(dlg):
    dlg.svc.setCurrentIndex(3)
    assert dlg.service_key == "google"
    assert not dlg.app_id.isEnabled()
    assert dlg.key.isEnabled()


def test_credentials_kept_per_service(dlg):
    dlg.svc.setCurrentIndex(1)
    dlg.app_id.setText("myid"); dlg.key.setText("mykey")
    dlg.svc.setCurrentIndex(0)  # 切走
    dlg.svc.setCurrentIndex(1)  # 切回
    assert dlg.app_id.text() == "myid"
    assert dlg.key.text() == "mykey"


def test_test_free_success(qapp, parent):
    client = FakeClient(result="很高兴见到你")
    d = TranslateServiceDialog(parent, Theme(False), ConfigManager(), client)
    d._do_test()
    assert _wait(qapp, lambda: "测试成功" in d.test_result.text())
    assert _wait(qapp, lambda: d._busy is False)
    assert TEST_SENTENCE in d.test_result.text()


def test_test_baidu_missing_creds(qapp, parent):
    d = TranslateServiceDialog(parent, Theme(False), ConfigManager(), FakeClient())
    d.svc.setCurrentIndex(1)  # baidu，空凭证
    d._do_test()
    assert _wait(qapp, lambda: "先填" in d.test_result.text())


def test_test_baidu_success(qapp, parent):
    client = FakeClient()
    d = TranslateServiceDialog(parent, Theme(False), ConfigManager(), client)
    d.svc.setCurrentIndex(1)
    d.app_id.setText("id"); d.key.setText("secret")
    d._do_test()
    assert _wait(qapp, lambda: "测试成功" in d.test_result.text())
    assert client.calls[0][0] == "baidu"
    assert client.calls[0][3] == "id"


def test_busy_guard(dlg):
    dlg._busy = True
    dlg._do_test()
    # 忙碌时不启动，文本不被改成测试中
    assert dlg.test_result.text() == ""


def test_save_writes_config(qapp, parent):
    d = TranslateServiceDialog(parent, Theme(False), ConfigManager(), FakeClient())
    d.svc.setCurrentIndex(1)
    d.app_id.setText("bid"); d.key.setText("bkey")
    d._do_save()
    qapp.processEvents()
    assert d.config.get("Translate", "Service") == "baidu"
    assert d.config.get("Translate", "BaiduAppId") == "bid"
    assert d.config.get("Translate", "BaiduKey") == "bkey"
