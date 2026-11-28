# -*- coding: utf-8 -*-
"""单实例守卫: 阻止第二个常驻进程，避免双托盘/热键双响应/文件互覆盖。"""
from __future__ import annotations

from . import IS_WINDOWS

ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "KIVO_SingleInstance_Mutex"


def _default_backend(name):
    """返回 (handle, last_error)。Windows 用命名互斥体，其他平台直接放行。"""
    if not IS_WINDOWS:
        return (1, 0)
    import ctypes
    k32 = ctypes.windll.kernel32
    handle = k32.CreateMutexW(None, False, name)
    return (handle, k32.GetLastError())


class SingleInstanceGuard:
    def __init__(self, name=MUTEX_NAME, backend=None):
        self.name = name
        self._backend = backend or _default_backend
        self._handle = None

    def acquire(self):
        """True=本实例可继续；False=已有实例在跑。任何异常都放行，绝不拦死正版。"""
        try:
            handle, err = self._backend(self.name)
        except Exception:
            return True
        if not handle:
            return True
        self._handle = handle  # 句柄留到进程结束，提前关闭等于放行
        return err != ERROR_ALREADY_EXISTS
