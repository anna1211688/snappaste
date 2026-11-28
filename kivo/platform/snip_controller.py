# -*- coding: utf-8 -*-
"""截图控制器: 抓屏 -> 覆盖层框选 -> 裁剪 -> 按模式分发 (保存/复制/翻译/回复)。

Qt 抓屏 (QScreen.grabWindow) 转 PIL, 与 AnnotationEditor 及后续 AI 看图衔接;
屏幕枚举与覆盖层工厂可注入, 裁剪为纯逻辑便于单测。多显示器按虚拟几何合并。
"""
from __future__ import annotations

import io
import os
import time

from PySide6.QtCore import QRect, QBuffer
from PySide6.QtWidgets import QApplication

from ..core import paths
from .snipper import SnipperOverlay


def pixmap_to_pil(pixmap):
    """QPixmap -> PIL Image (RGBA)。"""
    from PIL import Image
    buf = QBuffer()
    buf.open(QBuffer.ReadWrite)
    pixmap.save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(buf.data())))


def virtual_geometry(screens):
    """多个屏幕几何的并集 (虚拟桌面), 返回 QRect。"""
    rect = QRect(screens[0].geometry())
    for screen in screens[1:]:
        rect = rect.united(screen.geometry())
    return rect


def grab_virtual(screens):
    """抓取虚拟桌面, 返回 (PIL 图, 虚拟原点 QPoint)。逐屏抓取后贴到同一画布。"""
    from PIL import Image
    vrect = virtual_geometry(screens)
    canvas = Image.new("RGB", (vrect.width(), vrect.height()))
    for screen in screens:
        g = screen.geometry()
        pm = screen.grabWindow(0)
        img = pixmap_to_pil(pm).convert("RGB")
        canvas.paste(img, (g.left() - vrect.left(), g.top() - vrect.top()))
    return canvas, vrect.topLeft()


def crop_rect(image, selection, origin):
    """按覆盖层本地选区 (tuple) + 虚拟原点裁剪 PIL 图, 返回新 PIL 图。"""
    left, top, right, bottom = selection
    return image.crop((left + origin.x(), top + origin.y(),
                       right + origin.x(), bottom + origin.y()))


def shots_dir():
    d = os.path.join(paths.BASE, "shots")
    os.makedirs(d, exist_ok=True)
    return d


def save_shot(image):
    """保存到 shots/shot_<时间戳>.png, 按历史上限清理, 返回文件路径。"""
    d = shots_dir()
    path = os.path.join(d, "shot_" + time.strftime("%Y%m%d_%H%M%S") + ".png")
    image.save(path)
    _enforce_max(d)
    return path


def _enforce_max(d):
    try:
        keep = int(io_string_max())
    except Exception:
        keep = 100
    files = [f for f in sorted(os.listdir(d), reverse=True)
             if f.lower().endswith(".png")]
    for name in files[keep:]:
        try:
            os.remove(os.path.join(d, name))
        except OSError:
            pass


def io_string_max():
    # 延迟导入避免循环; 配置由 ConfigManager 经 runtime 传入更稳妥, 这里给默认
    return "100"


class SnipController:
    def __init__(self, theme, screens=None, overlay_factory=None):
        self.theme = theme
        self._screens = screens
        self._overlay_factory = overlay_factory or (
            lambda on_pick, on_cancel: SnipperOverlay(theme, on_pick, on_cancel))
        self._overlay = None
        self._image = None
        self._origin = None
        self.mode = "region"
        self.on_result = None

    def begin(self, mode="region", on_result=None):
        screens = self._screens or QApplication.screens()
        if not screens:
            return False
        self.mode = mode
        self.on_result = on_result
        self._image, self._origin = grab_virtual(screens)
        vrect = virtual_geometry(screens)
        self._overlay = self._overlay_factory(self._on_pick, self._on_cancel)
        self._overlay.begin(vrect)
        return True

    def _on_pick(self, selection):
        cropped = crop_rect(self._image, selection, self._origin)
        result = {"mode": self.mode, "image": cropped}
        if self.on_result is not None:
            self.on_result(result)
        self._cleanup()

    def _on_cancel(self):
        self._cleanup()

    def _cleanup(self):
        self._overlay = None
        self._image = None
