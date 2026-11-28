# -*- coding: utf-8 -*-
"""配置管理: Config.ini 加载、默认值、热键常量、保留注释的原地保存。"""
from __future__ import annotations

import configparser
import io
import os

from . import paths
from .util import atomic_write, ini_scalar, log_crash

DEFAULT_HOTKEYS = {"HotKey8": "F6", "HotKey9": "F7", "HotKey10": "F8",
                   "HotKey11": "F9", "HotKey12": "SHIFT+F9"}
DEFAULT_SNIP_KEYS = {"SnipKey": "F1", "PinKey": "F3", "CopyKey": "F5", "TransKey": "F4",
                     "ReplyKey": "SHIFT+F4", "MiniTransKey": "F10", "CopyTransKey": "F11",
                     "DelayKey": "无", "ClosePinsKey": "无", "TogglePinsKey": "无",
                     "RestorePinKey": "无", "ClickThroughKey": "无"}


class ConfigManager:
    def __init__(self):
        self.cfg = self._load()

    # ---------- 加载 ----------
    def _fresh(self) -> configparser.ConfigParser:
        hk_defaults = {f"HotKey{i}": "无" for i in range(13)}
        hk_defaults.update(DEFAULT_HOTKEYS)
        defaults = {
            "Config": {"SleepTime": "80", "WaveSet": "0", "AutoRun": "0",
                       "Language": "Chinese", "PasteEnter": "0", "PasteRemove": "1",
                       "MiniFormTime": "5", "MiniFormSet": "0", "AddChar": "1",
                       "LetterSet": "0", "ShowHotKey": "F2", "QuickPanelKey": "F12",
                       "SelectAiKey": "ctrl+alt+a"},
            "HotKey": hk_defaults, "Snip": dict(DEFAULT_SNIP_KEYS),
            "OCHotKey": {"HotKey": "无", "OCAutoSet": "0"}}
        c = configparser.ConfigParser(strict=False, interpolation=None)
        c.read_dict(defaults)
        return c

    def _load(self) -> configparser.ConfigParser:
        if not os.path.exists(paths.CONFIG_PATH):
            return self._fresh()
        for enc in ("utf-8-sig", "gbk"):
            c = self._fresh()
            try:
                c.read(paths.CONFIG_PATH, encoding=enc)
                return c
            except Exception:
                continue
        return self._fresh()

    # ---------- 访问 ----------
    def get(self, section: str, key: str, fallback=None):
        return self.cfg.get(section, key, fallback=fallback)

    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        try:
            return self.cfg.getint(section, key, fallback=fallback)
        except Exception:
            return fallback

    def set(self, section: str, key: str, value):
        if not self.cfg.has_section(section):
            self.cfg.add_section(section)
        self.cfg.set(section, key, str(value))

    def has_section(self, section: str) -> bool:
        return self.cfg.has_section(section)

    @property
    def sleep_ms(self) -> int:
        return max(10, self.getint("Config", "SleepTime", 80))

    # ---------- 保存 ----------
    def save(self):
        try:
            self._save_inner()
        except Exception:
            import sys
            log_crash("save-config", *sys.exc_info())

    def _save_inner(self):
        for sec in self.cfg.sections():
            for k, v in list(self.cfg.items(sec)):
                if v is not None and ini_scalar(v) != v:
                    self.cfg.set(sec, k, ini_scalar(v))
        if not os.path.exists(paths.CONFIG_PATH):
            buf = io.StringIO()
            self.cfg.write(buf)
            atomic_write(paths.CONFIG_PATH, buf.getvalue())
            return

        with open(paths.CONFIG_PATH, "rb") as cf:
            raw = cf.read()
        lines = []
        for enc in ("utf-8-sig", "gbk"):
            try:
                lines = raw.decode(enc).splitlines()
                break
            except Exception:
                lines = []
        pending = {(sec, k.lower()): v for sec in self.cfg.sections()
                   for k, v in self.cfg.items(sec)}
        out, cur = [], None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                cur = stripped[1:-1].strip()
            elif cur and "=" in line and not stripped.startswith((";", "#")):
                key = line.split("=", 1)[0].strip().lower()
                if (cur, key) in pending:
                    line = f"{line.split('=', 1)[0].strip()}={pending.pop((cur, key))}"
            out.append(line)

        by_sec = {}
        for (sec, k), v in pending.items():
            by_sec.setdefault(sec, []).append((k, v))
        for sec, items in by_sec.items():
            headers = [i for i, ln in enumerate(out)
                       if ln.strip().lower() == f"[{sec.lower()}]"]
            if headers:
                nxt = next((i for i in range(headers[0] + 1, len(out))
                            if out[i].strip().startswith("[")), len(out))
                out[nxt:nxt] = [f"{k}={v}" for k, v in items]
            else:
                out += [f"[{sec}]"] + [f"{k}={v}" for k, v in items]
        atomic_write(paths.CONFIG_PATH, "\n".join(out) + "\n")
