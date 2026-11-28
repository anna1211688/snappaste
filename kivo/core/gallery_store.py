# -*- coding: utf-8 -*-
"""截图历史画廊数据层: 文件列举、删除、标签。"""
from __future__ import annotations

import os

GALLERY_MAX = 60
_IMG_EXTS = (".png", ".gif")


def list_files(shots_dir):
    """返回倒序的图片文件名（最新在前）。目录不存在时返回空列表。"""
    try:
        return [f for f in sorted(os.listdir(shots_dir), reverse=True)
                if f.lower().endswith(_IMG_EXTS)]
    except OSError:
        return []


def cell_label(name):
    """生成格子下方短标签：GIF 前缀 + 截取时间片段。"""
    if name.lower().endswith(".gif"):
        prefix = "GIF "
    else:
        prefix = ""
    if name.startswith("shot_"):
        return prefix + name[5:20]
    return prefix + name[4:19]


def delete_file(shots_dir, name):
    try:
        os.remove(os.path.join(shots_dir, name))
        return True
    except OSError:
        return False


def delete_all(shots_dir):
    """删除全部图片，返回成功删除的数量。"""
    n = 0
    for name in list_files(shots_dir):
        if delete_file(shots_dir, name):
            n += 1
    return n
