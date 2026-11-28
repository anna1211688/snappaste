# -*- coding: utf-8 -*-
"""应用运行时控制器: 组装并驱动托盘/全局热键/编辑动作/窗口生命周期。

后台线程 (热键/托盘/粘贴) 的回调一律经 UiBridge 回主线程;
平台能力 (input_sim/tray/hotkey_listener) 可注入, 便于非 Windows 单测。
截图/贴图/快捷面板/迷你窗在后续批次挂入本控制器的对应方法。
"""
from __future__ import annotations

import threading

from PySide6.QtWidgets import QApplication

from ..platform import input_sim
from ..platform.tray import TrayController
from ..platform.hotkey_listener import HotkeyListener
from ..platform.single_instance import SingleInstanceGuard
from .runtime_bridge import UiBridge


class AppRuntime:
    def __init__(self, services, window, bridge=None, tray_factory=None,
                 hotkey_listener=None, instance_guard=None, beeper=None):
        self.services = services
        self.config = services.config
        self.window = window
        self.bridge = bridge or UiBridge()
        self.beeper = beeper or self._beep
        self._paste_busy = False
        self._pins = []
        self._tray = None

        # 单实例守卫: 已有实例时由 app.py 决定退出, 这里只暴露结果
        self.instance_guard = instance_guard or SingleInstanceGuard()
        self.single_instance_ok = self.instance_guard.acquire()

        # 动作表: (section, key) -> 主线程回调
        self.action_map = self._build_action_map()

        # 全局热键
        self.hotkeys = hotkey_listener or HotkeyListener(
            self.config, self.action_map)

        # 托盘 (可注入工厂便于测试)
        self._tray_factory = tray_factory

    # ---------- 生命周期 ----------
    def start(self):
        self.hotkeys.start()
        self._setup_tray()
        self.window.close_requested = self._on_close_request

    def stop(self):
        try:
            self.hotkeys.stop()
        finally:
            if self._tray is not None:
                self._tray.stop()
                self._tray = None

    def _setup_tray(self):
        icon_image = self._tray_icon_image()
        actions = {
            "show": self.show_main, "snip": self.snip_region,
            "snip_copy": self.snip_copy, "snip_trans": self.snip_translate,
            "snip_reply": self.snip_reply, "mini": self.show_mini_translate,
            "pin": self.pin_clipboard, "quit": self.quit_app,
        }
        controller = (self._tray_factory(actions, icon_image, self.bridge.post)
                      if self._tray_factory else
                      TrayController(actions, icon_image, self.bridge.post))
        if controller.start():
            self._tray = controller

    def _tray_icon_image(self):
        try:
            from ..ui.icons import load_tray_icon
            return load_tray_icon()
        except Exception:
            return None

    # ---------- 窗口行为 ----------
    def show_main(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def toggle_main(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.show_main()

    def _on_close_request(self, event):
        # 托盘可用: 隐藏而非退出; 无托盘: 接受关闭真正退出
        if self._tray is not None:
            event.ignore()
            self.window.hide()
        else:
            event.accept()

    def quit_app(self):
        self.stop()
        QApplication.quit()

    # ---------- 编辑类热键 ----------
    def act_select_all(self):
        if not input_sim.foreground_is_self():
            input_sim.send_combo(0x41)

    def act_cut(self):
        if not input_sim.foreground_is_self():
            input_sim.send_combo(0x58)

    def act_copy(self):
        if not input_sim.foreground_is_self():
            input_sim.send_combo(0x43)

    def act_paste(self):
        if not input_sim.foreground_is_self():
            input_sim.send_combo(0x56)

    def act_power_paste(self):
        text = self._clip_get()
        if text and not input_sim.foreground_is_self():
            input_sim.type_text(text)

    # ---------- 多次剪切 / 多次复制 ----------
    def multi_cut(self):
        self._multi_copy(cut=True)

    def multi_copy(self, cut=False):
        self._multi_copy(cut=cut)

    def _multi_copy(self, cut):
        def grab():
            text = ""
            try:
                before = self._clip_get()
                if not input_sim.foreground_is_self():
                    input_sim.send_combo(0x58 if cut else 0x43)
                    import time
                    deadline = time.time() + 0.5
                    while time.time() < deadline:
                        now = self._clip_get()
                        if now != before:
                            break
                        time.sleep(0.015)
                text = self._clip_get() or ""
            except Exception:
                text = ""
            self.bridge.post(lambda t=text: self._multi_apply(t))
        threading.Thread(target=grab, daemon=True).start()

    def _multi_apply(self, text):
        store = self.services.clip_store
        before = len(store.records)
        lines = [ln for ln in (text or "").splitlines() if ln.strip()]
        if len(lines) > 1:
            for ln in lines:
                store.add(ln)
        else:
            store.add(text)
        store.save()
        if len(store.records) > before:
            self.beeper()

    # ---------- 顺序粘贴 / 全部粘贴 ----------
    def paste_next(self):
        store = self.services.clip_store
        if not store.records or self._paste_busy:
            return
        if store.paste_index >= len(store.records):
            store.paste_index = 0
        idx = store.paste_index
        rec = store.records[idx]
        enter = self.config.get("Config", "PasteEnter", "0") == "1"
        self._paste_busy = True
        text = rec["text"]

        def work():
            ok = self._paste_text(text, enter=enter)
            self.bridge.post(lambda p=ok: self._paste_next_apply(idx, p))
        threading.Thread(target=work, daemon=True).start()

    def _paste_text(self, text, enter=False):
        try:
            self._clip_set(text)
            if input_sim.foreground_is_self():
                return False
            import time
            time.sleep(0.03)
            if input_sim.foreground_process_name() in ("et.exe", "wps.exe", "wpp.exe"):
                ok = bool(input_sim.type_text(text))
            else:
                ok = bool(input_sim.send_combo(0x56))
            if ok and enter:
                time.sleep(0.15)
                input_sim.send_enter()
            if ok:
                self.beeper()
            return ok
        except Exception:
            return False

    def _paste_next_apply(self, idx, ok):
        store = self.services.clip_store
        self._paste_busy = False
        if idx >= len(store.records) or store.paste_index != idx:
            return
        rec = store.records[idx]
        consume = self.config.get("Config", "PasteRemove", "1") == "1"
        if ok and consume and not rec["locked"]:
            store.delete(idx)
            if store.paste_index >= len(store.records):
                store.paste_index = 0
            store.save()
        elif ok:
            store.paste_index += 1

    def paste_all(self):
        store = self.services.clip_store
        if not store.records or self._paste_busy:
            return
        text = "\n".join(r["text"] for r in store.records)
        self._paste_busy = True

        def work():
            self._paste_text(text)
            self.bridge.post(self._paste_all_done)
        threading.Thread(target=work, daemon=True).start()

    def _paste_all_done(self):
        self._paste_busy = False

    # ---------- 删除 ----------
    def delete_last(self):
        store = self.services.clip_store
        for i in range(len(store.records) - 1, -1, -1):
            if not store.records[i]["locked"]:
                store.delete(i)
                store.save()
                return

    def delete_all(self):
        self.services.clip_store.delete_all()
        self.services.clip_store.save()

    # ---------- 截图/贴图/快捷/迷你 (后续批次实现) ----------
    def snip_region(self):
        raise NotImplementedError

    def snip_copy(self):
        raise NotImplementedError

    def snip_translate(self):
        raise NotImplementedError

    def snip_reply(self):
        raise NotImplementedError

    def pin_clipboard(self):
        raise NotImplementedError

    def show_mini_translate(self):
        raise NotImplementedError

    # ---------- 基础设施 ----------
    def _build_action_map(self):
        return {
            ("Config", "ShowHotKey"): self.toggle_main,
            ("Config", "QuickPanelKey"): self.open_quick_panel,
            ("Config", "SelectAiKey"): self.select_ai,
            ("HotKey", "HotKey1"): self.act_select_all,
            ("HotKey", "HotKey2"): self.act_cut,
            ("HotKey", "HotKey3"): self.act_copy,
            ("HotKey", "HotKey4"): self.act_paste,
            ("HotKey", "HotKey5"): self.act_power_paste,
            ("HotKey", "HotKey7"): self.multi_cut,
            ("HotKey", "HotKey8"): self.multi_copy,
            ("HotKey", "HotKey9"): self.paste_next,
            ("HotKey", "HotKey10"): self.paste_all,
            ("HotKey", "HotKey11"): self.delete_last,
            ("HotKey", "HotKey12"): self.delete_all,
            ("Snip", "SnipKey"): self.snip_region,
            ("Snip", "PinKey"): self.pin_clipboard,
            ("Snip", "CopyKey"): self.snip_copy,
            ("Snip", "TransKey"): self.snip_translate,
            ("Snip", "ReplyKey"): self.snip_reply,
            ("Snip", "MiniTransKey"): self.show_mini_translate,
            ("Snip", "CopyTransKey"): self.copy_trans,
            ("Snip", "DelayKey"): self.snip_delayed,
            ("Snip", "ClosePinsKey"): self.close_all_pins,
            ("Snip", "TogglePinsKey"): self.toggle_pins,
            ("Snip", "RestorePinKey"): self.restore_pin,
            ("Snip", "ClickThroughKey"): self.toggle_clickthrough,
            ("OCHotKey", "HotKey"): self.toggle_hotkeys,
        }

    def open_quick_panel(self):
        raise NotImplementedError

    def select_ai(self):
        raise NotImplementedError

    def copy_trans(self):
        raise NotImplementedError

    def snip_delayed(self):
        raise NotImplementedError

    def close_all_pins(self):
        for pin in list(self._pins):
            pin.close()
        self._pins = []

    def toggle_pins(self):
        visible = any(p.isVisible() for p in self._pins)
        for pin in self._pins:
            pin.setVisible(not visible)

    def restore_pin(self):
        raise NotImplementedError

    def toggle_clickthrough(self):
        raise NotImplementedError

    def toggle_hotkeys(self):
        if self.hotkeys.active_count:
            self.hotkeys.stop()
        else:
            self.hotkeys.start()

    # ---------- 剪贴板/提示音 ----------
    def _clip_get(self):
        return QApplication.clipboard().text()

    def _clip_set(self, text):
        QApplication.clipboard().setText(text)

    def _beep(self):
        try:
            if self.config.get("Wave", "WaveSet",
                               fallback=self.config.get("Config", "WaveSet", "0")) == "1":
                import winsound
                from ..core.paths import BASE
                winsound.PlaySound(
                    BASE + "\\ding.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass
