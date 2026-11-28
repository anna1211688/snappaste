# -*- coding: utf-8 -*-
"""画廊数据层与面板测试。"""
import os

from PySide6.QtWidgets import QFrame

from kivo.core import gallery_store
from kivo.ui.theme import Theme
from kivo.ui.panels.gallery_panel import GalleryPanel


def _make_png(shots_dir, name):
    from PIL import Image
    os.makedirs(shots_dir, exist_ok=True)
    Image.new("RGB", (200, 120), (52, 120, 246)).save(os.path.join(shots_dir, name))


def test_list_files(tmp_path):
    d = str(tmp_path / "shots")
    _make_png(d, "shot_001.png")
    _make_png(d, "shot_002.png")
    with open(os.path.join(d, "note.txt"), "w") as f:
        f.write("x")
    files = gallery_store.list_files(d)
    assert files == ["shot_002.png", "shot_001.png"]


def test_list_missing_dir(tmp_path):
    assert gallery_store.list_files(str(tmp_path / "nope")) == []


def test_cell_label():
    # name[5:20] 截断，含扩展名（与 Tk 版行为一致）
    assert gallery_store.cell_label("shot_abcdef.png") == "abcdef.png"
    assert gallery_store.cell_label("shot_x.gif").startswith("GIF ")


def test_delete_file(tmp_path):
    d = str(tmp_path / "shots")
    _make_png(d, "shot_001.png")
    assert gallery_store.delete_file(d, "shot_001.png")
    assert gallery_store.list_files(d) == []


def test_delete_all(tmp_path):
    d = str(tmp_path / "shots")
    _make_png(d, "shot_001.png")
    _make_png(d, "shot_002.png")
    assert gallery_store.delete_all(d) == 2
    assert gallery_store.list_files(d) == []


def test_panel_renders_cells(qapp, tmp_path):
    d = str(tmp_path / "shots")
    _make_png(d, "shot_001.png")
    _make_png(d, "shot_002.png")
    p = GalleryPanel(Theme(False), d)
    p.show()
    qapp.processEvents()
    # 两个格子
    assert p.grid.count() == 2


def test_panel_empty(qapp, tmp_path):
    d = str(tmp_path / "shots")
    os.makedirs(d)
    p = GalleryPanel(Theme(False), d)
    p.show()
    qapp.processEvents()
    # 空态盒存在
    boxes = [w for w in p.container.findChildren(QFrame) if w.objectName() == "emptyBox"]
    assert len(boxes) == 1


def test_pin_callback(qapp, tmp_path):
    d = str(tmp_path / "shots")
    _make_png(d, "shot_001.png")
    pinned = []
    p = GalleryPanel(Theme(False), d, pin_callback=lambda n: pinned.append(n))
    p._pin("shot_001.png")
    assert pinned == ["shot_001.png"]


def test_delete_one_refreshes(qapp, tmp_path):
    d = str(tmp_path / "shots")
    _make_png(d, "shot_001.png")
    p = GalleryPanel(Theme(False), d)
    p.show()
    p._delete_one("shot_001.png")
    qapp.processEvents()
    assert p.grid.count() == 1  # 只剩空态盒
