# -*- coding: utf-8 -*-
"""系统托盘控制器测试。"""
from PIL import Image

from kivo.platform.tray import TrayController, TRAY_MENU


class FakeMenuItem:
    def __init__(self, text, handler, default=False):
        self.text = text; self.handler = handler; self.default = default


class FakeMenu:
    SEPARATOR = "SEP"

    def __init__(self, *items):
        self.items = items


class FakeIcon:
    def __init__(self, name, image, tooltip, menu):
        self.name = name; self.image = image; self.tooltip = tooltip
        self.menu = menu; self.ran = False; self.stopped = False

    def run(self):
        self.ran = True

    def stop(self):
        self.stopped = True


class FakePystray:
    Menu = FakeMenu

    def __init__(self):
        self.icons = []

    def MenuItem(self, text, handler, default=False):
        return FakeMenuItem(text, handler, default)

    def Icon(self, name, image, tooltip, menu):
        ic = FakeIcon(name, image, tooltip, menu)
        self.icons.append(ic)
        return ic


def _controller(factory):
    invoked = []
    actions = {k: (lambda kk=k: invoked.append(kk))
               for k in ("show", "snip", "snip_copy", "snip_trans",
                         "snip_reply", "mini", "pin", "quit")}
    img = Image.new("RGB", (32, 32), "blue")
    c = TrayController(actions, img, invoke=lambda fn: fn(), factory=factory)
    return c, invoked


def test_menu_spec():
    c, _ = _controller(FakePystray())
    spec = c.menu_spec()
    assert len(spec) == len(TRAY_MENU)
    assert spec[0] == ("tray.show", "show", True)


def test_build_menu_items():
    p = FakePystray()
    c, _ = _controller(p)
    menu = c.build_menu()
    # 7 个动作 + 分隔 + 退出
    texts = [i.text for i in menu.items if isinstance(i, FakeMenuItem)]
    assert "退出 KIVO" in texts
    assert len(texts) == 8


def test_menu_handler_invokes_action():
    p = FakePystray()
    c, invoked = _controller(p)
    menu = c.build_menu()
    first = menu.items[0]
    assert isinstance(first, FakeMenuItem)
    first.handler()
    assert invoked == ["show"]


def test_start_creates_icon():
    p = FakePystray()
    c, _ = _controller(p)
    assert c.start() is True
    assert len(p.icons) == 1
    assert p.icons[0].name == "KIVO"


def test_stop_icon():
    p = FakePystray()
    c, _ = _controller(p)
    c.start()
    c.stop()
    assert p.icons[0].stopped is True


def test_missing_pystray_degrades():
    c = TrayController({}, Image.new("RGB", (16, 16)),
                       invoke=lambda fn: fn(), factory=None)
    assert c.available is False
    assert c.start() is False


def test_invoke_marshals():
    p = FakePystray()
    marshalled = []
    actions = {"show": lambda: marshalled.append("ran")}
    c = TrayController(actions, Image.new("RGB", (16, 16)),
                       invoke=lambda fn: marshalled.append("queued"),
                       factory=p)
    menu = c.build_menu()
    menu.items[0].handler()
    # 回调先经 invoke 排队（此处 invoke 不立即执行 action）
    assert marshalled == ["queued"]
