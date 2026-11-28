# -*- coding: utf-8 -*-
"""二维码生成弹窗。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QTextEdit, QLabel, QFileDialog

from .base import Dialog
from ..components import PrimaryButton, SecondaryButton
from ...core import qr_store


def pil_to_pixmap(img):
    rgb = img.convert("RGB")
    data = rgb.tobytes("raw", "RGB")
    qimg = QImage(data, rgb.width, rgb.height, rgb.width * 3,
                  QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class QrDialog(Dialog):
    def __init__(self, parent):
        super().__init__(parent, "二维码生成", width=420)
        self._pil = None

        self.input = QTextEdit()
        self.input.setObjectName("qrInput")
        self.input.setFixedHeight(90)
        self.input.setPlaceholderText("输入文本或链接…")
        self.body.addWidget(self.input)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedHeight(240)
        self.body.addWidget(self.preview)

        gen = PrimaryButton("生成二维码")
        gen.clicked.connect(self._make)
        copy = SecondaryButton("复制图片")
        copy.clicked.connect(self._copy)
        save = SecondaryButton("保存图片")
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
            self, "保存二维码", "qrcode.png", "PNG (*.png)")
        if path:
            self._pil.save(path)
