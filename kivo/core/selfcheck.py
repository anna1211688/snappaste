# -*- coding: utf-8 -*-
"""软件自检数据层: 各检查项解耦，可注入依赖，返回 (ok, extra)。"""
from __future__ import annotations

import json
import os
import tempfile

from .i18n import tr

# (key, 标签 i18n key)
CHK_ITEMS = [
    ("data", "chk.data"),
    ("config", "chk.config"),
    ("records", "chk.records"),
    ("ocr", "chk.ocr"),
    ("translate", "chk.translate"),
    ("hotkey", "chk.hotkey"),
]


def check_data_writable(base_dir):
    try:
        fd, p = tempfile.mkstemp(dir=base_dir)
        try:
            os.write(fd, b"ok")
        finally:
            os.close(fd)
            os.remove(p)
        return True, ""
    except OSError as e:
        return False, str(e)[:50]


def check_config(config_path):
    try:
        import configparser
        cp = configparser.ConfigParser(strict=False, interpolation=None)
        cp.read(config_path, encoding="utf-8-sig")
        return len(cp.sections()) > 0, ""
    except Exception as e:  # 含 UnicodeDecodeError(GBK 老配置)等: 自检项只应报告失败, 不应崩溃
        return False, str(e)[:50]


def check_records(records_path):
    for p in (records_path, records_path + ".bak"):
        try:
            with open(p, encoding="utf-8") as f:
                if isinstance(json.loads(f.read()), list):
                    return True, ""
        except (OSError, ValueError):
            continue
    return False, ""


class SelfCheckRunner:
    """组装各检查项；外部依赖（OCR/翻译/热键）以可调用对象注入。"""

    def __init__(self, base_dir, config_path, records_path,
                 ocr_provider=None, translate_provider=None,
                 hotkey_provider=None):
        self.base_dir = base_dir
        self.config_path = config_path
        self.records_path = records_path
        self.ocr_provider = ocr_provider
        self.translate_provider = translate_provider
        self.hotkey_provider = hotkey_provider

    def run(self):
        results = {}
        results["data"] = check_data_writable(self.base_dir)
        results["config"] = check_config(self.config_path)
        results["records"] = check_records(self.records_path)
        results["ocr"] = self._external(self.ocr_provider)
        results["translate"] = self._external(self.translate_provider)
        results["hotkey"] = self._hotkey()
        return results

    @staticmethod
    def _external(provider):
        if provider is None:
            return False, ""
        try:
            return provider() is not None, ""
        except Exception as e:  # 外部组件探测失败：标记异常而非崩溃
            return False, str(e)[:50]

    def _hotkey(self):
        if self.hotkey_provider is None:
            return False, tr("chk.hotkey_missing")
        try:
            n = self.hotkey_provider()
            if n:
                return True, tr("chk.hotkey_count", n=n)
            return False, tr("chk.hotkey_missing")
        except OSError as e:
            return False, str(e)[:50]
