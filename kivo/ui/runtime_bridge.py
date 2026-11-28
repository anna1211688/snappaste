# -*- coding: utf-8 -*-
"""跨线程 UI 桥: 任意线程把回调投递到主线程事件循环执行。

替代 Tkinter 版的 15ms UI 队列轮询: 热键/托盘/截图都在后台线程触发,
Qt 控件只能在主线程访问, 经信号 (Auto/Queued 连接) 自动 marshal。
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from ..core.util import log_crash


class UiBridge(QObject):
    invoked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoked.connect(self._run)

    def _run(self, fn):
        try:
            fn()
        except Exception as exc:  # 回调异常绝不能炸事件循环
            log_crash("ui-bridge", exc)

    def post(self, fn):
        """可在任意线程调用; 信号按连接类型排队到主线程。"""
        self.invoked.emit(fn)
