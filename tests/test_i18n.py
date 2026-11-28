# -*- coding: utf-8 -*-
"""i18n 机制单测 + 英文模式零中文残留（遍历全部面板与设置）。"""
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QComboBox, QTextEdit

from kivo.core import paths, i18n
from kivo.core.voice import TRANS_TARGETS
from kivo.ui.theme import Theme
from kivo.app_context import Services
from kivo.ui.panels.settings_panel import SettingsPanel


def has_cjk(text):
    return any("一" <= ch <= "鿿" for ch in (text or ""))


# 语言选择器允许保留的语言原生名（中文/繁體中文/日本語…）
_NATIVE_LANG_NAMES = {name for name, _code in TRANS_TARGETS}

_PATH_NAMES = ("CONFIG_PATH", "RECORDS_PATH", "PHRASES_PATH", "AI_CHATS_PATH",
               "AI_MEMORY_PATH", "AI_PROMPTS_PATH", "PROJECTS_PATH",
               "CALC_HISTORY_PATH", "CRASH_LOG_PATH")
_PANEL_KEYS = ("ai", "voice", "trans", "clip", "phrases", "project", "fx",
               "clock", "calc", "dl", "pomo", "winman", "batch", "dev")


def _visible_texts(root):
    out = []
    for w in root.findChildren(QWidget):
        for getter in ("text", "placeholderText", "toolTip", "windowTitle"):
            fn = getattr(w, getter, None)
            if callable(fn):
                try:
                    out.append(fn())
                except Exception:
                    pass
        if isinstance(w, QComboBox):
            out.extend(w.itemText(i) for i in range(w.count()))
        if isinstance(w, QTextEdit):
            out.append(w.toPlainText())
    for action in root.findChildren(QAction):
        out.append(action.text())
        out.append(action.toolTip())
    out.append(root.windowTitle())
    return out


# ---------- 隔离：路径重定向 + 结束恢复中文 ----------

def _install_isolation(tmp_path, monkeypatch):
    for name in _PATH_NAMES:
        monkeypatch.setattr(paths, name, str(tmp_path / f"{name}.dat"))
    monkeypatch.setattr(paths, "SHOTS_DIR", str(tmp_path / "shots"))


# ---------- 单元行为 ----------

def test_no_missing_translations(tmp_path, monkeypatch):
    _install_isolation(tmp_path, monkeypatch)
    missing = i18n.missing_keys()
    assert missing["zh"] == []
    assert missing["en"] == []


def test_language_switch_changes_text(tmp_path, monkeypatch):
    _install_isolation(tmp_path, monkeypatch)
    i18n.set_language(i18n.ZH)
    zh = i18n.tr("common.save")
    i18n.set_language(i18n.EN)
    en = i18n.tr("common.save")
    assert zh == "保存"
    assert en == "Save"
    assert zh != en
    i18n.set_language(i18n.ZH)


def test_format_kwargs(tmp_path, monkeypatch):
    _install_isolation(tmp_path, monkeypatch)
    i18n.set_language(i18n.EN)
    assert i18n.tr("dl.download_pct", pct=42) == "Downloading 42%"
    i18n.set_language(i18n.ZH)


def test_unknown_key_falls_back_to_key(tmp_path, monkeypatch):
    _install_isolation(tmp_path, monkeypatch)
    assert i18n.tr("no.such.key") == "no.such.key"


# ---------- 英文模式零残留 ----------

def test_english_panels_have_no_chinese(qapp, tmp_path, monkeypatch):
    _install_isolation(tmp_path, monkeypatch)
    i18n.set_language(i18n.EN)
    services = Services()
    theme = Theme(False)
    services.make_main_services(theme)

    leaked = {}
    for key in _PANEL_KEYS:
        panel = services.pane_factory(key)
        panel.show()
        qapp.processEvents()
        bad = {t for t in _visible_texts(panel)
               if has_cjk(t) and t not in _NATIVE_LANG_NAMES}
        if bad:
            leaked[key] = sorted(bad)

    settings = SettingsPanel(theme, services.config)
    settings.show()
    qapp.processEvents()
    bad = {t for t in _visible_texts(settings)
           if has_cjk(t) and t not in _NATIVE_LANG_NAMES}
    if bad:
        leaked["settings"] = sorted(bad)

    i18n.set_language(i18n.ZH)
    assert not leaked, f"Chinese text remains in English mode: {leaked}"
