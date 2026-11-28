# -*- coding: utf-8 -*-
"""二维码生成数据层: 封装 qrcode，返回 PIL 图像。"""
from __future__ import annotations


def generate_qr(text):
    """生成二维码 PIL RGB 图像；缺 qrcode 库时抛 RuntimeError。"""
    try:
        import qrcode
    except ImportError:
        raise RuntimeError("缺少 qrcode 库，请先 pip install qrcode")
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")
