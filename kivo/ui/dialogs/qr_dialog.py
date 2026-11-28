# -*- coding: utf-8 -*-
"""二维码生成弹窗。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QTextEdit, QLabel, QFileDialog

from .base import Dialog
from ..components import PrimaryButton, SecondaryButton
from ...core import qr_store
from ...core.i18n import tr


def pil_to_pixmap(img):
    rgb = img.convert("RGB")
    data = rgb.tobytes("raw", "RGB")
    qimg = QImage(data, rgb.width, rgb.height, rgb.width * 3,
                  QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class QrDialog(Dialog):
    def __init__(self, parent):
        super().__init__(parent, tr("qr.title"), width=420)
        self._pil = None

        self.input = QTextEdit()
        self.input.setObjectName("qrInput")
        self.input.setFixedHeight(90)
        self.input.setPlaceholderText(tr("qr.ph"))
        self.body.addWidget(self.input)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedHeight(240)
        self.body.addWidget(self.preview)

        gen = PrimaryButton(tr("qr.gen"), icon_name="qr")
        gen.clicked.connect(self._make)
        copy = SecondaryButton(tr("qr.copy_img"), icon_name="copy")
        copy.clicked.connect(self._copy)
        save = SecondaryButton(tr("qr.save_img"), icon_name="save")
        save.clicked.connect(self._save)
        self.add_button(save); self.add_button(copy); self.add_button(gen)

    def _make(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        try:
            self._pil = qr_store.generate_qr(text)
        except RuntimeError as e:
            self.preview.setText(str(e)); return
        self._pix = pil_to_pixmap(self._pil)
        self.preview.setPixmap(self._pix)

    def _copy(self):
        if self._pil is None:
            return
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setPixmap(self._pix)

    def _save(self):
        if self._pil is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("qr.save_title"), "qrcode.png", "PNG (*.png)")
        if path:
            self._pil.save(path)
