# -*- coding: utf-8 -*-
"""异步写盘调度器测试。"""
import os

import pytest

from kivo.core import data


@pytest.fixture
def async_mode():
    # 开启异步, 测试结束后恢复同步并停止后台线程, 避免污染其他测试
    data.set_async(True)
    yield
    data.set_async(False)
    data.shutdown_async()


def test_flush_writes_file_and_bak(async_mode, tmp_path):
    path = str(tmp_path / "a.json")
    payload = [{"x": 1}, {"y": "中文"}]
    data.save_json(path, payload)
    # flush 后内容与备份均落盘
    assert data.flush_all()
    assert data.load_json(path, []) == payload
    assert os.path.exists(path + ".bak")


def test_consecutive_same_path_keeps_latest(async_mode, tmp_path):
    path = str(tmp_path / "b.json")
    for i in range(20):
        data.save_json(path, {"v": i})
    assert data.flush_all()
    assert data.load_json(path, {}) == {"v": 19}


def test_multiple_paths(async_mode, tmp_path):
    targets = {}
    for name in ("c1", "c2", "c3"):
        p = str(tmp_path / f"{name}.json")
        data.save_json(p, {"name": name})
        targets[name] = p
    assert data.flush_all()
    for name, p in targets.items():
        assert data.load_json(p, {}) == {"name": name}


def test_returns_to_sync_after_disable(tmp_path):
    path = str(tmp_path / "d.json")
    data.set_async(True)
    data.save_json(path, {"v": 1})
    data.set_async(False)
    data.shutdown_async()
    # 同步模式下无需 flush, 立即能读到
    assert data.load_json(path, {}) == {"v": 1}


def test_store_save_uses_async(async_mode, tmp_path):
    from kivo.core.clip_store import ClipStore
    path = str(tmp_path / "records.json")
    store = ClipStore(path)
    store.add("异步落盘")
    store.save()
    assert data.flush_all()
    assert ClipStore(path).records[0]["text"] == "异步落盘"
