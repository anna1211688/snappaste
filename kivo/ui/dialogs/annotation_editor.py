# -*- coding: utf-8 -*-
"""标注编辑器: 截图后画矩形/箭头/马赛克/文字等，支持撤销重做与多种完成动作。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup,
    QSpinBox, QInputDialog,
)
from PySide6.QtGui import QPixmap

from ...core import annotation as A
from ..theme import SPACING
from ..components import PrimaryButton, SecondaryButton, GhostButton

TOOL_LABELS = [
    ("矩形", "rect"), ("椭圆", "ellipse"), ("箭头", "arrow"), ("直线", "line"),
    ("画笔", "pen"), ("文字", "text"), ("序号", "seq"),
    ("马赛克", "mosaic"), ("模糊", "blur"),
]
MAX_DISPLAY_W, MAX_DISPLAY_H = 1500, 880


class Canvas(QLabel):
    """标注画布，把鼠标事件以显示坐标发出。"""

    pressed = Signal(QPoint)
    moved = Signal(QPoint)
    released = Signal(QPoint)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed.emit(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.moved.emit(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.released.emit(event.position().toPoint())


class AnnotationEditor(QDialog):
    def __init__(self, base_img, theme, callbacks=None, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._base = base_img.convert("RGB")
        self._callbacks = callbacks or {}
        self.stack = A.OpStack()
        self.current_tool = "rect"
        self.current_color = A.DEFAULT_COLOR

        w, h = self._base.size
        self.scale = min(1.0, MAX_DISPLAY_W / w, MAX_DISPLAY_H / h)
        self.dw = max(1, int(w * self.scale))
        self.dh = max(1, int(h * self.scale))

        self._start = None
        self._points = []
        self._cur_end = None

        self.setWindowTitle("标注 - 画完点「完成并钉图」")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self._build_ui()
        self._refresh()

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING["md"], SPACING["md"],
                                SPACING["md"], SPACING["md"])
        root.setSpacing(SPACING["sm"])

        bar = QHBoxLayout()
        bar.setSpacing(6)
        self.tool_group = QButtonGroup(self)
        for label, key in TOOL_LABELS:
            b = QPushButton(label)
            b.setObjectName("annoTool")
            b.setCheckable(True)
            b.setChecked(key == self.current_tool)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._set_tool(k))
            self.tool_group.addButton(b)
            bar.addWidget(b)

        bar.addSpacing(8)
        self.color_group = QButtonGroup(self)
        for i, cname in enumerate(A.PALETTE):
            sw = QPushButton()
            sw.setObjectName("annoSwatch")
            sw.setCheckable(True)
            sw.setFixedSize(24, 24)
            sw.setStyleSheet(f"background:{cname};")
            sw.setChecked(cname == self.current_color)
            sw.setCursor(Qt.PointingHandCursor)
            sw.clicked.connect(lambda _=False, c=cname: self._set_color(c))
            self.color_group.addButton(sw)
            bar.addWidget(sw)

        bar.addSpacing(8)
        bar.addWidget(QLabel("线宽"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(A.WIDTH_MIN, A.WIDTH_MAX)
        self.width_spin.setValue(A.DEFAULT_WIDTH)
        bar.addWidget(self.width_spin)
        bar.addStretch()
        root.addLayout(bar)

        self.canvas = Canvas()
        self.canvas.setObjectName("annoCanvas")
        self.canvas.setFixedSize(self.dw, self.dh)
        self.canvas.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.canvas.pressed.connect(self._on_press)
        self.canvas.moved.connect(self._on_move)
        self.canvas.released.connect(self._on_release)
        root.addWidget(self.canvas)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        self.undo_btn = SecondaryButton("撤销", icon_name="undo")
        self.undo_btn.clicked.connect(self._undo)
        self.redo_btn = SecondaryButton("重做")
        self.redo_btn.clicked.connect(self._redo)
        self.clear_btn = GhostButton("清空标注", icon_name="trash")
        self.clear_btn.clicked.connect(self._clear)
        self.ocr_btn = GhostButton("OCR 识别文字")
        self.ocr_btn.clicked.connect(lambda: self._invoke("ocr"))
        self.code_btn = GhostButton("扫二维码/条码", icon_name="qr")
        self.code_btn.clicked.connect(lambda: self._invoke("code"))
        for b in (self.undo_btn, self.redo_btn, self.clear_btn,
                  self.ocr_btn, self.code_btn):
            bottom.addWidget(b)
        bottom.addStretch()

        self.discard_btn = GhostButton("放弃", icon_name="close")
        self.discard_btn.clicked.connect(self._discard)
        self.save_only_btn = SecondaryButton("只保存不钉图", icon_name="save")
        self.save_only_btn.clicked.connect(lambda: self._finish("save"))
        self.save_as_btn = SecondaryButton("另存为", icon_name="save")
        self.save_as_btn.clicked.connect(lambda: self._finish("save_as"))
        self.copy_btn = SecondaryButton("复制到剪贴板", icon_name="copy")
        self.copy_btn.clicked.connect(lambda: self._finish("copy"))
        self.pin_btn = PrimaryButton("完成并钉图", icon_name="check")
        self.pin_btn.clicked.connect(lambda: self._finish("pin"))
        for b in (self.discard_btn, self.save_only_btn, self.save_as_btn,
                  self.copy_btn, self.pin_btn):
            bottom.addWidget(b)
        root.addLayout(bottom)

    # ---------- 状态 ----------
    def _set_tool(self, key):
        self.current_tool = key

    def _set_color(self, cname):
        self.current_color = cname

    def _to_img(self, pos):
        return (int(pos.x() / self.scale), int(pos.y() / self.scale))

    def _refresh(self):
        rendered = A.render_ops(self._base, self.stack.ops)
        if self.scale < 1.0:
            rendered = rendered.resize((self.dw, self.dh))
        self.canvas.setPixmap(self._to_qpixmap(rendered))

    @staticmethod
    def _to_qpixmap(pil_img):
        if pil_img.mode != "RGBA":
            pil_img = pil_img.convert("RGBA")
        data, size = pil_img.tobytes("raw", "RGBA"), pil_img.size
        from PySide6.QtGui import QImage
        qimg = QImage(data, size[0], size[1], QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimg.copy())

    # ---------- 鼠标 ----------
    def _on_press(self, pos):
        self._start = self._to_img(pos)
        self._points = [self._start]
        self._cur_end = self._start
        if self.current_tool == "text":
            text, ok = QInputDialog.getText(self, "文字标注", "输入文字:")
            if ok and text:
                self.stack.add(A.make_text_op(
                    self._start, text, self.current_color,
                    self.width_spin.value()))
                self._refresh()
            self._start = None
        elif self.current_tool == "seq":
            self.stack.add(A.make_seq_op(
                self._start, self.stack.next_seq_number(),
                self.current_color, self.width_spin.value()))
            self._refresh()
            self._start = None

    def _on_move(self, pos):
        if self._start is None:
            return
        img_pt = self._to_img(pos)
        self._cur_end = img_pt
        if self.current_tool == "pen":
            self._points.append(img_pt)

    def _on_release(self, pos):
        if self._start is None:
            return
        end = self._to_img(pos)
        tool = self.current_tool
        if tool == "pen":
            self.stack.add(A.make_pen_op(self._points, self.current_color,
                                         self.width_spin.value()))
        elif tool in A.SHAPE_TOOLS:
            self.stack.add(A.make_shape_op(
                tool, self._start + end, self.current_color,
                self.width_spin.value()))
        self._start = None
        self._points = []
        self._refresh()

    # ---------- 编辑动作 ----------
    def _undo(self):
        if self.stack.undo():
            self._refresh()

    def _redo(self):
        if self.stack.redo():
            self._refresh()

    def _clear(self):
        self.stack.clear()
        self._refresh()

    def result_image(self):
        return A.render_ops(self._base, self.stack.ops)

    def _invoke(self, key):
        fn = self._callbacks.get(key)
        if fn:
            fn(self.result_image())

    def _finish(self, action):
        image = self.result_image()
        fn = self._callbacks.get(action)
        if fn:
            fn(image)
        self.accept()

    def _discard(self):
        fn = self._callbacks.get("discard")
        if fn:
            fn()
        self.reject()
