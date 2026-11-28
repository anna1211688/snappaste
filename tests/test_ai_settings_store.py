# -*- coding: utf-8 -*-
"""AI 模型中心数据层测试。"""
import json

import pytest

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.core import ai_settings_store as astore
from kivo.core.ai import AI_PRESETS


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


def test_empty_profiles_has_all_services():
    p = astore.empty_profiles()
    assert set(p) == set(AI_PRESETS)
    assert all(v == [] for v in p.values())


def test_load_missing_returns_empty():
    p = astore.load_profiles(ConfigManager())
    assert set(p) == set(AI_PRESETS)


def test_load_bad_json_returns_empty():
    cfg = ConfigManager()
    cfg.set("AI", "ModelProfiles", "{not json")
    p = astore.load_profiles(cfg)
    assert all(v == [] for v in p.values())


def test_load_dedup_and_truncate():
    payload = {"zhipu": [
        {"model": "a", "enabled": True},
        {"model": "a", "enabled": False},  # 重复
        {"model": "b"},
        "bad-row",
    ]}
    cfg = ConfigManager()
    cfg.set("AI", "ModelProfiles", json.dumps(payload))
    p = astore.load_profiles(cfg)
    models = [x["model"] for x in p["zhipu"]]
    assert models == ["a", "b"]


def test_add_model():
    p = astore.empty_profiles()
    assert astore.add_model(p, "zhipu", "glm-x") is True
    assert astore.add_model(p, "zhipu", "glm-x") is False  # 去重
    assert astore.add_model(p, "nope", "m") is False
    assert astore.add_model(p, "zhipu", "  ") is False


def test_add_model_truncates_long_id():
    p = astore.empty_profiles()
    long_id = "m" * 300
    astore.add_model(p, "zhipu", long_id)
    assert len(p["zhipu"][0]["model"]) == astore.MODEL_ID_MAX


def test_remove_model():
    p = astore.empty_profiles()
    astore.add_model(p, "zhipu", "m")
    assert astore.remove_model(p, "zhipu", "m") is True
    assert astore.remove_model(p, "zhipu", "m") is False


def test_toggle_model():
    p = astore.empty_profiles()
    astore.add_model(p, "zhipu", "m")
    assert p["zhipu"][0]["enabled"] is True
    assert astore.toggle_model(p, "zhipu", "m") is True
    assert p["zhipu"][0]["enabled"] is False


def test_write_then_load_roundtrip():
    cfg = ConfigManager()
    p = astore.empty_profiles()
    astore.add_model(p, "openai", "gpt-4o")
    astore.write_profiles(cfg, p)
    again = astore.load_profiles(cfg)
    assert again["openai"][0]["model"] == "gpt-4o"


def test_load_routes_empty():
    r = astore.load_routes(ConfigManager())
    assert all(v == ("", "") for v in r.values())


def test_save_and_load_routes_roundtrip():
    cfg = ConfigManager()
    routes = {"RouteChat": ("openai", "gpt-4o"), "RouteText": ("", "")}
    astore.save_routes(cfg, routes)
    back = astore.load_routes(cfg)
    assert back["RouteChat"] == ("openai", "gpt-4o")
    assert back["RouteText"] == ("", "")


def test_save_routes_illegal_svc_treated_as_follow():
    cfg = ConfigManager()
    astore.save_routes(cfg, {"RouteChat": ("ghost", "m")})
    assert astore.load_routes(cfg)["RouteChat"] == ("", "")


def test_route_defs_count():
    assert len(astore.ROUTE_DEFS) == 5
