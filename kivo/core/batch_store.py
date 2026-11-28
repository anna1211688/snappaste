# -*- coding: utf-8 -*-
"""图片批量处理数据层: 尺寸/格式/质量/水印，Pillow 处理逻辑（不依赖 UI）。"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont


def target_size(w, h, percent=100, max_side=0):
    nw = max(1, int(round(w * percent / 100.0)))
    nh = max(1, int(round(h * percent / 100.0)))
    if max_side and max(nw, nh) > max_side:
        scale = max_side / float(max(nw, nh))
        nw, nh = max(1, int(nw * scale)), max(1, int(nh * scale))
    return nw, nh


def output_path(src, out_dir, forced_fmt, used):
    stem = os.path.splitext(os.path.basename(src))[0]
    if forced_fmt:
        ext = {"jpg": ".jpg", "png": ".png", "webp": ".webp"}[forced_fmt]
    else:
        ext = os.path.splitext(src)[1] or ".jpg"
    candidate = os.path.join(out_dir, stem + ext)
    i = 1
    while candidate.lower() in used or os.path.exists(candidate):
        candidate = os.path.join(out_dir, f"{stem}_{i}{ext}")
        i += 1
    used.add(candidate.lower())
    return candidate


def validate_options(percent, max_side, quality):
    if not (1 <= percent <= 500) or max_side < 0:
        return False
    if not (1 <= quality <= 100):
        return False
    return True


def process_one(src, opts, out_dir, used):
    with Image.open(src) as im:
        im.load()
        nw, nh = target_size(im.width, im.height,
                             opts["percent"], opts["max_side"])
        out = im.resize((nw, nh), Image.Resampling.LANCZOS)
        if opts.get("watermark"):
            ImageDraw.Draw(out).text(
                (8, max(1, nh - 14)), opts["watermark"],
                fill=opts.get("wm_color", "#FF0000"),
                font=ImageFont.load_default())
        path = output_path(src, out_dir, opts["format"], used)
        if path.lower().endswith((".jpg", ".jpeg")):
            if out.mode != "RGB":
                bg = Image.new("RGB", out.size, (255, 255, 255))
                if out.mode in ("RGBA", "LA"):
                    bg.paste(out, mask=out.split()[-1])
                else:
                    bg.paste(out.convert("RGB"))
                out = bg
            out.save(path, quality=opts["quality"])
        elif path.lower().endswith(".webp"):
            out.save(path, quality=opts["quality"])
        else:
            out.save(path)
        return path


class BatchStore:
    def run_all(self, files, opts, out_dir, on_progress=None):
        os.makedirs(out_dir, exist_ok=True)
        used = set()
        ok, errors = 0, []
        total = len(files)
        for i, src in enumerate(files, 1):
            try:
                process_one(src, opts, out_dir, used)
                ok += 1
            except Exception as e:  # 单张失败不中断整批，收集错误
                errors.append(f"{os.path.basename(src)}: {e}")
            if on_progress:
                on_progress(i, total)
        return ok, errors
