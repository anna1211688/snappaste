# -*- coding: utf-8 -*-
"""系统托盘: pystray 图标与菜单，回调 marshal 回主线程，缺库安全降级。"""
from __future__ import annotations

# (显示名, 动作键, 是否默认项)
TRAY_MENU = [
    ("显示主窗口", "show", True),
    ("区域截图", "snip", False),
    ("截图并复制", "snip_copy", False),
    ("截图翻译", "snip_trans", False),
    ("智能回复", "snip_reply", False),
    ("迷你翻译", "mini", False),
    ("贴剪贴板内容", "pin", False),
]


def _default_factory():
    try:
        import pystray
        return pystray
    except Exception:
        return None


class TrayController:
    def __init__(self, actions, icon_image, invoke, factory=None, tooltip="KIVO 智能工作台"):
        # actions: {key: callable}; invoke: callable(fn) marshal 到主线程
        self.actions = actions
        self.icon_image = icon_image
        self.invoke = invoke
        self._pystray = factory if factory is not None else _default_factory()
        self.tooltip = tooltip
        self._icon = None

    def menu_spec(self):
        return list(TRAY_MENU)

    def build_menu(self):
        p = self._pystray
        items = []
        for label, key, is_default in TRAY_MENU:
            def make(act_key):
                def handler(_icon=None, _item=None):
                    fn = self.actions.get(act_key)
                    if fn:
                        self.invoke(fn)
                return handler
            items.append(p.MenuItem(label, make(key), default=is_default))
        items.append(p.Menu.SEPARATOR)
        items.append(p.MenuItem("退出 KIVO",
                                lambda _i=None, _it=None: self.invoke(self.actions["quit"])))
        return p.Menu(*items)

    def start(self):
        if self._pystray is None:
            return False
        try:
            self._icon = self._pystray.Icon(
                "KIVO", self.icon_image, self.tooltip, self.build_menu())
            import threading
            threading.Thread(target=self._icon.run, daemon=True,
                             name="kivo-tray").start()
            return True
        except Exception:
            self._icon = None
            return False

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    @property
    def available(self):
        return self._pystray is not None
