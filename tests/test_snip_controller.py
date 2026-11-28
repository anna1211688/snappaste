# -*- coding: utf-8 -*-
"""snip_controller 纯逻辑测试: 虚拟几何/裁剪/保存, 注入假屏幕。"""
import pytest
from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QPixmap, QColor

from kivo.platform import snip_controller as sc


@pytest.fixture(autouse=True)
def _app(qapp):
    yield


class _FakeScreen:
    def __init__(self, rect):
        self._rect = QRect(*rect)

    def geometry(self):
        return QRect(self._rect)

    def grabWindow(self, _h):
        pm = QPixmap(self._rect.width(), self._rect.height())
        pm.fill(QColor("#80A0C0"))
        return pm


def test_virtual_geometry_single():
    r = sc.virtual_geometry([_FakeScreen((0, 0, 1920, 1080))])
    assert (r.left(), r.top(), r.width(), r.height()) == (0, 0, 1920, 1080)


def test_virtual_geometry_multi_monitor():
    screens = [_FakeScreen((0, 0, 1920, 1080)),
               _FakeScreen((1920, 0, 1280, 1024))]
    r = sc.virtual_geometry(screens)
    assert (r.left(), r.top(), r.width(), r.height()) == (0, 0, 3200, 1080)


def test_grab_and_crop():
    img, origin = sc.grab_virtual([_FakeScreen((0, 0, 200, 100))])
    assert origin == QPoint(0, 0)
    cropped = sc.crop_rect(img, (10, 10, 60, 50), origin)
    assert cropped.size == (50, 40)


def test_crop_with_negative_origin():
    screens = [_FakeScreen((-100, 0, 200, 100))]
    img, origin = sc.grab_virtual(screens)
    assert origin.x() == -100
    cropped = sc.crop_rect(img, (0, 0, 50, 50), origin)
    # 本地 0 对应全局 -100
    assert cropped.size == (50, 50)


def test_save_shot(tmp_path, monkeypatch):
    monkeypatch.setattr(sc.paths, "BASE", str(tmp_path))
    img, _origin = sc.grab_virtual([_FakeScreen((0, 0, 60, 40))])
    path = sc.save_shot(img)
    assert path.endswith(".png")
    import os
    assert os.path.exists(path)
