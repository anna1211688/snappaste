# -*- coding: utf-8 -*-
"""热键数据层测试。"""
import pytest

from kivo.core import paths
from kivo.core.config import ConfigManager
from kivo.core import hotkey_store as hs


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "Config.ini"))


@pytest.mark.parametrize("raw,expected", [
    ("", None), (None, None), ("无", None), ("None", None),
    ("CTRL+ALT+V", "ctrl+alt+v"), ("f6", "f6"),
    ("Control + C", "ctrl+c"), ("Windows+D", "win+d"),
    ("请按键…", None), ("a b", "ab"), ("ctrl+", "ctrl"),
])
def test_normalize(raw, expected):
    assert hs.normalize_hotkey(raw) == expected


def test_normalize_illegal_chars():
    assert hs.normalize_hotkey("ctrl+@") is None


def test_current_value_missing():
    cfg = ConfigManager()
    assert hs.current_value(cfg, "Config", "NotExist") == "无"


def test_current_value_existing():
    cfg = ConfigManager()
    cfg.set("Config", "ShowHotKey", "F2")
    assert hs.current_value(cfg, "Config", "ShowHotKey") == "F2"


def test_find_conflicts():
    pairs = [(("Config", "A"), "f1"), (("Snip", "B"), "f1"),
             (("HotKey", "C"), "f6")]
    conf = hs.find_conflicts(pairs)
    assert set(conf["f1"]) == {("Config", "A"), ("Snip", "B")}
    assert "f6" not in conf


def test_apply_mapping_writes():
    cfg = ConfigManager()
    mapping = {("Config", "ShowHotKey"): "ctrl+q", ("Snip", "SnipKey"): "无"}
    normalized, conflicts = hs.apply_mapping(cfg, mapping)
    assert conflicts == {}
    assert cfg.get("Config", "ShowHotKey") == "CTRL+Q"
    assert cfg.get("Snip", "SnipKey") == "无"


def test_apply_mapping_conflict_last_wins():
    cfg = ConfigManager()
    a, b = ("Config", "ShowHotKey"), ("Snip", "SnipKey")
    mapping = {a: "f1", b: "f1"}
    _normalized, conflicts = hs.apply_mapping(cfg, mapping)
    assert "f1" in conflicts
    # 后设（b 顺序在 HOTKEY_ACTIONS 中更靠后）保留，先设清空
    assert cfg.get("Snip", "SnipKey") == "F1"
    assert cfg.get("Config", "ShowHotKey") == "无"


def test_default_mapping():
    m = hs.default_mapping()
    assert m[("Config", "ShowHotKey")] == "F2"
    assert m[("HotKey", "HotKey8")] == "F6"
    assert m[("Snip", "SnipKey")] == "F1"
    assert m[("Snip", "DelayKey")] == "无"


def test_build_mapping_roundtrip():
    cfg = ConfigManager()
    cfg.set("Config", "ShowHotKey", "F2")
    m = hs.build_mapping(cfg)
    assert m[("Config", "ShowHotKey")] == "F2"
    # 未配置项归一为无
    assert m[("Snip", "DelayKey")] == "无"


def test_actions_count():
    # 27 个配置项，含全局切换
    assert len(hs.HOTKEY_ACTIONS) == 27
    assert ("OCHotKey", "HotKey", "全局切换热键") in hs.HOTKEY_ACTIONS
