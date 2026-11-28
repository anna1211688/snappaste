# -*- coding: utf-8 -*-
"""核心逻辑层单元测试 (不联网、不依赖桌面)。"""
import json
import os

import pytest

from kivo.core import util, network, data
from kivo.core.config import ConfigManager, DEFAULT_HOTKEYS, DEFAULT_SNIP_KEYS


# ---------- util ----------
class TestUtil:
    def test_ini_scalar_folds_whitespace(self):
        assert util.ini_scalar("a\nb\t  c") == "a b c"

    def test_ini_scalar_plain_unchanged(self):
        assert util.ini_scalar("hello") == "hello"

    def test_redact_bearer(self):
        assert util.redact_secrets("Bearer abc.def-123/==") == "Bearer ***"

    def test_redact_sk_key(self):
        assert util.redact_secrets("token sk-ABCDEFGH12345") == "token sk-***"

    def test_redact_url_key(self):
        out = util.redact_secrets("https://x.test/api?key=SECRET123&q=1")
        assert "SECRET123" not in out
        assert "key=***" in out

    def test_redact_ai_detail_authorization(self):
        out = util.redact_ai_detail('Authorization: Bearer xyz123')
        assert "xyz123" not in out

    def test_redact_ai_detail_known_shapes(self):
        assert "***" in util.redact_ai_detail("key sk-ABCDEF123456")
        assert "***" in util.redact_ai_detail("AIza1234567890abcdefghij")

    def test_redact_ai_detail_secret_fallback(self):
        out = util.redact_ai_detail("the raw secret appears", secret="raw secret")
        assert "raw secret" not in out

    def test_atomic_write_roundtrip(self, tmp_path):
        p = str(tmp_path / "f.txt")
        util.atomic_write(p, "内容\n第二行")
        assert open(p, encoding="utf-8").read() == "内容\n第二行"
        assert not os.path.exists(p + ".tmp")


# ---------- network ----------
class TestNetwork:
    def test_normalize_adds_scheme(self):
        assert network.normalize_manual_proxy("127.0.0.1:7890") == "http://127.0.0.1:7890"

    def test_normalize_keeps_scheme(self):
        assert network.normalize_manual_proxy("https://1.2.3.4:8080") == "https://1.2.3.4:8080"

    def test_normalize_rejects_missing_port(self):
        assert network.normalize_manual_proxy("127.0.0.1") == ""

    def test_normalize_rejects_bad_scheme(self):
        assert network.normalize_manual_proxy("socks5://127.0.0.1:1080") == ""

    def test_normalize_empty(self):
        assert network.normalize_manual_proxy("") == ""

    def test_set_proxy_config_validates(self):
        network.set_proxy_config("off")
        # 非法模式回退 system
        network.set_proxy_config("bogus", "x")
        from kivo.core import network as net
        assert net._PROXY_CFG["mode"] == "system"


# ---------- data ----------
class TestData:
    def test_save_load_roundtrip(self, tmp_path):
        p = str(tmp_path / "x.json")
        payload = [{"a": 1}, {"b": "中文"}]
        data.save_json(p, payload)
        assert data.load_json(p, []) == payload
        assert os.path.exists(p + ".bak")

    def test_load_falls_back_to_bak(self, tmp_path):
        p = str(tmp_path / "x.json")
        data.save_json(p, {"v": 1})
        with open(p, "w") as f:
            f.write("{broken json")
        assert data.load_json(p, None) == {"v": 1}

    def test_load_default_when_missing(self, tmp_path):
        p = str(tmp_path / "missing.json")
        assert data.load_json(p, "dflt") == "dflt"

    def test_validator_rejects_bad_shape(self, tmp_path):
        p = str(tmp_path / "x.json")
        data.save_json(p, {"wrong": True})
        assert data.load_json(p, "d", validator=lambda o: isinstance(o, list)) == "d"


# ---------- config ----------
@pytest.fixture
def cfg_manager(tmp_path, monkeypatch):
    monkeypatch.setattr("kivo.core.config.paths.CONFIG_PATH", str(tmp_path / "Config.ini"))
    return ConfigManager()


class TestConfig:
    def test_defaults_loaded(self, cfg_manager):
        assert cfg_manager.get("Config", "Language") == "Chinese"
        assert cfg_manager.sleep_ms == 80

    def test_default_hotkeys_present(self, cfg_manager):
        assert cfg_manager.get("HotKey", "HotKey8") == DEFAULT_HOTKEYS["HotKey8"]
        assert cfg_manager.get("Snip", "SnipKey") == DEFAULT_SNIP_KEYS["SnipKey"]

    def test_set_save_reload(self, cfg_manager):
        cfg_manager.set("Config", "SleepTime", "120")
        cfg_manager.save()
        new = ConfigManager()
        assert new.sleep_ms == 120

    def test_sleep_ms_floor(self, cfg_manager):
        cfg_manager.set("Config", "SleepTime", "0")
        cfg_manager.save()
        assert ConfigManager().sleep_ms >= 10

    def test_save_preserves_comments(self, cfg_manager, monkeypatch):
        from kivo.core import config as cfgmod
        path = cfgmod.paths.CONFIG_PATH
        with open(path, "w", encoding="utf-8") as f:
            f.write("; 保留这条注释\n[Config]\nSleepTime=80\nLanguage=Chinese\n")
        m = ConfigManager()
        m.set("Config", "SleepTime", "99")
        m.save()
        text = open(path, encoding="utf-8").read()
        assert "保留这条注释" in text
        assert "SleepTime=99" in text

    def test_new_section_appended(self, cfg_manager):
        cfg_manager.set("Network", "ProxyMode", "off")
        cfg_manager.save()
        reloaded = ConfigManager()
        assert reloaded.get("Network", "ProxyMode") == "off"
