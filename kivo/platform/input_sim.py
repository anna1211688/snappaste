# -*- coding: utf-8 -*-
"""Win32 输入模拟: 全局热键动作里的全选/剪切/复制/粘贴/强力粘贴/回车。

Windows 用 SendInput (带扫描码, WPS 类窗口才认) -> keybd_event -> keyboard 三层兜底;
非 Windows 安全降级。纯逻辑 (type_units) 可在任何平台单测。
"""
from __future__ import annotations


from . import IS_WINDOWS

VK_CONTROL = 0x11
VK_RETURN = 0x0D
KEYUP = 0x0002
KEYUNICODE = 0x0004

# 组合键 vk -> keyboard 包键名
_COMBO_NAMES = {0x41: "ctrl+a", 0x58: "ctrl+x", 0x43: "ctrl+c", 0x56: "ctrl+v"}


def type_units(text):
    """逐字输入的 UTF-16 码元展开 (unit, vk, up, unicode):
    增补平面字符是代理对, 直接 ord 截断会出错字; 换行/制表符走 vk。纯逻辑。"""
    out = []
    for ch in text:
        if ch == "\r":
            continue
        if ch == "\n":
            out += [(0, VK_RETURN, False, False), (0, VK_RETURN, True, False)]
        elif ch == "\t":
            out += [(0, 0x09, False, False), (0, 0x09, True, False)]
        else:
            b = ch.encode("utf-16-le")
            for k in range(0, len(b), 2):
                unit = b[k] | (b[k + 1] << 8)
                out += [(unit, 0, False, True), (unit, 0, True, True)]
    return out


def _build_input_structures():
    """构造 Win32 SendInput 结构 (完整 union, x64 下 sizeof 必须为 40)。"""
    import ctypes
    from ctypes import wintypes

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = (("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)))

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = (("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)))

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = (("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                    ("wParamH", wintypes.WORD))

    class INPUTUNION(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT))

    class INPUT(ctypes.Structure):
        _fields_ = (("type", wintypes.DWORD), ("u", INPUTUNION))

    return INPUT


def scan(vk):
    """虚拟键码 -> 硬件扫描码; 无扫描码的模拟按键会被部分窗口忽略。"""
    if not IS_WINDOWS:
        return 0
    try:
        import ctypes
        return ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    except Exception:
        return 0


def _key_event(INPUT, vk, up=False, unicode_unit=0):
    i = INPUT()
    i.type = 1
    if unicode_unit:
        i.u.ki.wVk = 0
        i.u.ki.wScan = unicode_unit
        i.u.ki.dwFlags = KEYUNICODE | (KEYUP if up else 0)
    else:
        i.u.ki.wVk = vk
        i.u.ki.wScan = scan(vk)
        i.u.ki.dwFlags = KEYUP if up else 0
    return i


def send_combo(vk_key):
    """向当前前台窗口发送 Ctrl+<vk>。三层兜底, 非 Windows 走 keyboard 包。"""
    if IS_WINDOWS:
        try:
            INPUT = _build_input_structures()
            seq = (INPUT * 4)(
                _key_event(INPUT, VK_CONTROL), _key_event(INPUT, vk_key),
                _key_event(INPUT, vk_key, True), _key_event(INPUT, VK_CONTROL, True))
            import ctypes
            if ctypes.windll.user32.SendInput(4, seq, ctypes.sizeof(INPUT)) == 4:
                return True
        except Exception:
            pass
        try:
            import ctypes
            u = ctypes.windll.user32
            u.keybd_event(VK_CONTROL, scan(VK_CONTROL), 0, 0)
            u.keybd_event(vk_key, scan(vk_key), 0, 0)
            u.keybd_event(vk_key, scan(vk_key), KEYUP, 0)
            u.keybd_event(VK_CONTROL, scan(VK_CONTROL), KEYUP, 0)
            return True
        except Exception:
            pass
    name = _COMBO_NAMES.get(vk_key)
    if name:
        try:
            import keyboard
            keyboard.send(name)
            return True
        except Exception:
            pass
    return False


def send_enter():
    """向当前前台窗口发送一次回车。"""
    if IS_WINDOWS:
        try:
            INPUT = _build_input_structures()
            seq = (INPUT * 2)(_key_event(INPUT, VK_RETURN),
                              _key_event(INPUT, VK_RETURN, True))
            import ctypes
            if ctypes.windll.user32.SendInput(2, seq, ctypes.sizeof(INPUT)) == 2:
                return True
        except Exception:
            pass
        try:
            import ctypes
            u = ctypes.windll.user32
            u.keybd_event(VK_RETURN, scan(VK_RETURN), 0, 0)
            u.keybd_event(VK_RETURN, scan(VK_RETURN), KEYUP, 0)
            return True
        except Exception:
            pass
    try:
        import keyboard
        keyboard.send("enter")
        return True
    except Exception:
        return False


def type_text(text):
    """逐字 Unicode 输入 (强力粘贴/屏蔽 Ctrl+V 的窗口); 返回是否成功。"""
    if not text:
        return False
    if IS_WINDOWS:
        try:
            INPUT = _build_input_structures()
            units = type_units(text)
            seq = (INPUT * len(units))(
                *[_key_event(INPUT, vk, up, unit) for unit, vk, up, _uc in units])
            import ctypes
            return ctypes.windll.user32.SendInput(
                len(units), seq, ctypes.sizeof(INPUT)) == len(units)
        except Exception:
            pass
    try:
        import keyboard
        keyboard.write(text)
        return True
    except Exception:
        return False


def foreground_is_self():
    """当前前台窗口是否属于本进程 (是本程序就不该往外发组合键)。"""
    if not IS_WINDOWS:
        return False
    try:
        import ctypes
        pid = ctypes.wintypes.DWORD()
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value == ctypes.windll.kernel32.GetCurrentProcessId()
    except Exception:
        return False


def foreground_process_name():
    """前台进程 exe 名 (小写), 用于 WPS 类窗口改走逐字输入。"""
    if not IS_WINDOWS:
        return ""
    try:
        import ctypes
        pid = ctypes.wintypes.DWORD()
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(260)
            size = ctypes.wintypes.DWORD(260)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                    h, 0, buf, ctypes.byref(size)):
                return buf.value.rsplit("\\", 1)[-1].lower()
        finally:
            ctypes.windll.kernel32.CloseHandle(h)
    except Exception:
        return ""
    return ""
