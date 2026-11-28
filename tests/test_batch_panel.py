# -*- coding: utf-8 -*-
"""图片批量处理数据层与面板测试。"""
from PIL import Image
import pytest

from kivo.core.batch_store import (
    BatchStore, target_size, output_path, validate_options, process_one,
)
from kivo.ui.theme import Theme
from kivo.ui.panels.batch_panel import BatchPanel


def _make_image(path, size=(100, 80), color=(20, 120, 200)):
    Image.new("RGB", size, color).save(path)


# ---------- 纯函数 ----------
def test_target_size_percent():
    assert target_size(100, 80, 50) == (50, 40)


def test_target_size_max_side():
    w, h = target_size(200, 100, 100, 50)
    assert max(w, h) == 50


def test_output_path(tmp_path):
    p = output_path(str(tmp_path / "a.png"), str(tmp_path), "jpg", set())
    assert p.endswith("a.jpg")


def test_output_path_dedup(tmp_path):
    used = set()
    p1 = output_path(str(tmp_path / "a.png"), str(tmp_path), "png", used)
    open(p1, "w").close()
    p2 = output_path(str(tmp_path / "a.png"), str(tmp_path), "png", used)
    assert p1 != p2


def test_validate_options():
    assert validate_options(100, 0, 88)
    assert not validate_options(0, 0, 88)
    assert not validate_options(100, -1, 88)
    assert not validate_options(100, 0, 101)


# ---------- 真实处理 ----------
def test_process_one_jpg(tmp_path):
    src = tmp_path / "src.png"
    _make_image(str(src))
    opts = {"percent": 50, "max_side": 0, "quality": 85,
            "format": "jpg", "watermark": "KIVO"}
    out = process_one(str(src), opts, str(tmp_path), set())
    assert out.endswith(".jpg")
    with Image.open(out) as im:
        assert im.size == (50, 40)


def test_process_one_keep_format(tmp_path):
    src = tmp_path / "src.png"
    _make_image(str(src))
    opts = {"percent": 100, "max_side": 0, "quality": 88,
            "format": "", "watermark": ""}
    out = process_one(str(src), opts, str(tmp_path), set())
    assert out.endswith(".png")


def test_run_all_mixed(tmp_path):
    good = tmp_path / "good.png"
    _make_image(str(good))
    bad = tmp_path / "bad.png"
    bad.write_text("not an image")
    out_dir = tmp_path / "out"
    opts = {"percent": 100, "max_side": 0, "quality": 88,
            "format": "png", "watermark": ""}
    ok, errors = BatchStore().run_all(
        [str(good), str(bad)], opts, str(out_dir))
    assert ok == 1
    assert len(errors) == 1


# ---------- 面板 ----------
@pytest.fixture
def bp(qapp):
    p = BatchPanel(Theme(False))
    p.show()
    qapp.processEvents()
    return p


def test_panel_bad_params(bp):
    bp.files = ["/tmp/x.png"]
    bp.percent.setText("abc")
    bp._run()
    assert bp._thread is None


def test_panel_no_files(bp):
    bp._run()
    assert bp._thread is None


def test_remove_files(bp):
    bp.files = ["/tmp/a.png", "/tmp/b.png"]
    bp.file_list.addItem("a.png")
    bp.file_list.addItem("b.png")
    bp.file_list.setCurrentRow(0)
    bp._remove_sel()
    assert bp.files == ["/tmp/b.png"]
