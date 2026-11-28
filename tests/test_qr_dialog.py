# -*- coding: utf-8 -*-
"""二维码数据层与弹窗测试。"""
import sys

from PySide6.QtWidgets import QWidget

from kivo.core import qr_store
from kivo.ui.dialogs.qr_dialog import QrDialog, pil_to_pixmap


import pytest


@pytest.fixture
def parent(qapp):
    w = QWidget()
    return w


def test_generate_qr():
    img = qr_store.generate_qr("https://example.com")
    assert img.size[0] > 0 and img.mode == "RGB"


def test_generate_missing_lib(monkeypatch):
    # 模拟 qrcode 不可导入
    monkeypatch.setitem(sys.modules, "qrcode", None)
    with pytest.raises(RuntimeError):
        qr_store.generate_qr("x")


def test_pil_to_pixmap(qapp):
    img = qr_store.generate_qr("hello")
    pm = pil_to_pixmap(img)
    assert not pm.isNull()


def test_dialog_render(qapp, parent):
    d = QrDialog(parent)
    d.show()
    qapp.processEvents()
    assert d.preview is not None


def test_dialog_make(qapp, parent):
    d = QrDialog(parent)
    d.input.setPlainText("测试内容")
    d._make()
    qapp.processEvents()
    assert d._pil is not None
    assert not d._pix.isNull()


def test_dialog_empty_no_make(qapp, parent):
    d = QrDialog(parent)
    d._make()
    assert d._pil is None


def test_dialog_copy(qapp, parent):
    d = QrDialog(parent)
    d.input.setPlainText("x")
    d._make()
    d._copy()
    from PySide6.QtWidgets import QApplication
    assert not QApplication.clipboard().pixmap().isNull()


def test_dialog_save(qapp, parent, tmp_path, monkeypatch):
    d = QrDialog(parent)
    d.input.setPlainText("x")
    d._make()
    target = str(tmp_path / "out.png")
    monkeypatch.setattr(
        "kivo.ui.dialogs.qr_dialog.QFileDialog.getSaveFileName",
        lambda *a, **k: (target, "PNG (*.png)"))
    d._save()
    import os
    assert os.path.exists(target)
