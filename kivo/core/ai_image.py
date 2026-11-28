# -*- coding: utf-8 -*-
"""AI 视觉输入图片处理: 统一长边缩放、JPEG 压缩、data URL。"""
from __future__ import annotations

import base64
import io

IMG_MAX_EDGE = 1568
IMG_QUALITY = 85


def fit_image(img):
    """转 RGB, 长边压到 IMG_MAX_EDGE 内 (已更小则原样)。img: PIL.Image。"""
    im = img.convert("RGB")
    w, h = im.size
    m = max(w, h)
    if m > IMG_MAX_EDGE:
        im = im.resize(
            (max(1, round(w * IMG_MAX_EDGE / m)),
             max(1, round(h * IMG_MAX_EDGE / m))),
            im.__class__ and __import__("PIL").Image.LANCZOS)
    return im


def image_dataurl(img):
    """PIL 图 -> JPEG data URL。"""
    im = fit_image(img)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=IMG_QUALITY)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
