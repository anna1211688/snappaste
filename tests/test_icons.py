# -*- coding: utf-8 -*-
"""线性符号图标测试。"""
import pytest

from PySide6.QtGui import QColor

from kivo.ui import icons
from kivo.ui.icon_paths import ICON_PATHS


@pytest.mark.parametrize("name", list(ICON_PATHS.keys()))
def test_every_icon_renders(qapp, name):
    ic = icons.icon(name)
    for px in (16, 20, 24, 48):
        pm = ic.pixmap(px, px)
        assert not pm.isNull()
        assert pm.width() == px
        # 存在非透明像素（确实画出了内容）
        assert not pm.hasAlphaChannel() or _has_opaque(pm)


def _has_opaque(pm):
    img = pm.toImage()
    for y in range(img.height()):
        for x in range(img.width()):
            if img.pixelColor(x, y).alpha() > 0:
                return True
    return False


def test_has_icon():
    assert icons.has_icon("gear")
    assert not icons.has_icon("nope")


def test_unknown_icon_raises(qapp):
    with pytest.raises(KeyError):
        icons.icon("missing")
    with pytest.raises(KeyError):
        icons.tinted_icon("missing", "#000000")


def test_tinted_svg_contains_color():
    data = bytes(icons._svg_bytes("gear", "#FF8800"))
    assert b"#FF8800" in data


def test_tinted_icon_pixels(qapp):
    ic = icons.tinted_icon("check", "#FF0000")
    pm = ic.pixmap(64, 64)
    img = pm.toImage()
    found = False
    target = QColor("#FF0000")
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() > 0 and abs(c.red() - target.red()) < 30 \
                    and c.green() < 90 and c.blue() < 90:
                found = True
                break
        if found:
            break
    assert found


def test_raw_pixmap(qapp):
    pm = icons._raw_pixmap("clock", size=32)
    assert pm.size().width() == 32
    assert _has_opaque(pm)


def test_tool_colors():
    main, soft = icons.tool_colors("ai")
    assert main.startswith("#") and soft.startswith("#")
    # 未知图标给默认配色而非报错
    assert icons.tool_colors("unknown") == ("#007AFF", "#E9F2FF")


def test_nav_item_toggle_icon(qapp):
    from kivo.ui.components import NavItem
    item = NavItem("k", "gear", "设置")
    item.setChecked(True)
    pm1 = item.icon().pixmap(24, 24)
    item.setChecked(False)
    pm2 = item.icon().pixmap(24, 24)
    assert not pm1.isNull() and not pm2.isNull()


def test_svg_template_shape():
    # 每个图标路径非空且是合法片段
    for name, body in ICON_PATHS.items():
        assert body.strip()
        assert "<" in body and "/>" in body


# ---------- 按钮图标支持 ----------
def test_primary_button_with_icon(qapp):
    from kivo.ui.components import PrimaryButton
    b = PrimaryButton("下载", icon_name="download")
    assert not b.icon().isNull()
    assert b.text() == "下载"


def test_button_without_icon_backward_compat(qapp):
    from kivo.ui.components import SecondaryButton
    b = SecondaryButton("纯文字")
    assert b.icon().isNull()


@pytest.mark.parametrize("cls", ["PrimaryButton", "SecondaryButton",
                                 "DangerButton", "GhostButton"])
def test_all_buttons_accept_icon(qapp, cls):
    import kivo.ui.components as comp
    b = getattr(comp, cls)("文字", icon_name="check")
    assert not b.icon().isNull()


# ---------- EmptyState ----------
def test_empty_state_basic(qapp):
    from kivo.ui.components import EmptyState
    from PySide6.QtWidgets import QLabel
    e = EmptyState("browser", "还没有图片", "点击添加")
    texts = [l.text() for l in e.findChildren(QLabel)]
    assert "还没有图片" in texts
    assert "点击添加" in texts


def test_empty_state_action(qapp):
    from kivo.ui.components import EmptyState
    clicked = []
    e = EmptyState("copy", "空", "副", action_text="添加",
                   on_action=lambda: clicked.append(1))
    e.show()
    qapp.processEvents()
    from kivo.ui.components import SecondaryButton
    btns = e.findChildren(SecondaryButton)
    assert btns and clicked == []
    btns[0].click()
    assert clicked == [1]
