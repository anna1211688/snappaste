# -*- coding: utf-8 -*-
"""KIVO 设计令牌与主题系统 (PySide6)。

颜色令牌沿用 Tkinter 版本已确认的 Apple HIG 冷调浅色 + 深色系统色, 集中定义一次, 组件一律引用。
所有可绘制样式集中在应用级 QSS, 用 objectName 选择器; 不在容器上内联 setStyleSheet (会切断子树级联)。
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# ---------- 圆角令牌 ----------
RADIUS = {"sm": 8, "md": 10, "lg": 14, "xl": 16, "pill": 999}

# ---------- 间距令牌 ----------
SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 20, "xxl": 28}

# ---------- 字体令牌 ----------
FONT_FAMILY = '"Segoe UI","Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif'
FONT_MONO = '"Cascadia Code","Consolas","Courier New",monospace'
FONT_SIZE = {"xs": 10, "sm": 11, "md": 12, "lg": 13, "xl": 15, "title": 20, "hero": 26}

# ---------- 浅色令牌 (与 main.py 一致) ----------
LIGHT = {
    "bg": "#F2F2F7", "surface": "#FFFFFF", "border": "#E5E5EA", "border_strong": "#D1D1D6",
    "text": "#000000", "text_2": "#3C3C43", "muted": "#8E8E93", "muted_2": "#AEAEB2",
    "accent": "#007AFF", "accent_hover": "#409CFF", "accent_press": "#0062CC",
    "accent_tint": "#E9F2FF", "accent_line": "#99C2FF", "sel_bg": "#D6E6FF",
    "head_bg": "#F5F5F7", "stripe": "#FAFAFC", "soft": "#EFEFF4",
    "danger": "#FF3B30", "danger_bg": "#FFEBE9", "danger_line": "#FFB4B0",
    "danger_hover": "#FFDCD9", "danger_press": "#FFC9C5",
    "hover": "#E5F0FF", "press": "#CCE4FF", "success": "#34C759",
    "side": "#F5F5F7", "side_text": "#3C3C43", "side_active": "#D1D1D6",
}

# ---------- 深色令牌 ----------
DARK = {
    "bg": "#1C1C1E", "surface": "#2C2C2E", "border": "#38383A", "border_strong": "#48484A",
    "text": "#FFFFFF", "text_2": "#EBEBF5", "muted": "#98989F", "muted_2": "#8E8E93",
    "accent": "#0A84FF", "accent_hover": "#5AAEFF", "accent_press": "#0066D6",
    "accent_tint": "#1E3A5F", "accent_line": "#2A6BB0", "sel_bg": "#3A5A80",
    "head_bg": "#2C2C2E", "stripe": "#242426", "soft": "#3A3A3C",
    "danger": "#FF453A", "danger_bg": "#5B211F", "danger_line": "#8A332E",
    "danger_hover": "#6E2A27", "danger_press": "#7A2F2C",
    "hover": "#33415C", "press": "#2C3E57", "success": "#30D158",
    "side": "#161617", "side_text": "#EBEBF5", "side_active": "#3A3A3C",
}


class Theme:
    """当前主题令牌访问 + QSS 生成。"""

    def __init__(self, dark: bool = False):
        self.dark = dark
        self.tokens = DARK if dark else LIGHT

    def c(self, key: str) -> str:
        return self.tokens[key]

    def qcolor(self, key: str) -> QColor:
        return QColor(self.tokens[key])

    def font(self, size_key: str = "md", bold: bool = False, mono: bool = False) -> QFont:
        f = QFont()
        f.setFamilies((FONT_MONO if mono else FONT_FAMILY).strip('"').split('","'))
        f.setPixelSize(FONT_SIZE[size_key])
        f.setBold(bold)
        return f

    # ---------- 基础 QSS (控件 objectName 规则; 各组件可在此扩展) ----------
    def base_qss(self) -> str:
        t = self.tokens
        return f"""
* {{ font-family: {FONT_FAMILY}; color: {t['text']}; }}
QWidget#root {{ background: {t['bg']}; }}
QFrame#card {{ background: {t['surface']}; border-radius: {RADIUS['xl']}px; }}
QFrame#pane {{ background: {t['surface']}; border-radius: {RADIUS['xl']}px; }}
QWidget#transparentPane {{ background: transparent; }}
QWidget#panelRoot {{ background: {t['bg']}; }}
QFrame#softCard {{ background: {t['soft']}; border-radius: {RADIUS['lg']}px; }}
QFrame#divider {{ background: {t['border']}; max-height: 1px; min-height:1px; }}
QLabel#sectionHead {{ color: {t['muted']}; background: transparent; font-size: {FONT_SIZE['sm']}px; font-weight: 600; }}
QLabel#blockHead {{ color: {t['text']}; background: transparent; font-size: {FONT_SIZE['md']}px; font-weight: 700; }}
QTextEdit#resultBox {{
    background: {t['stripe']}; border: 1px solid {t['border']}; border-radius: {RADIUS['sm']}px;
    font-size: {FONT_SIZE['md']}px; padding: 8px;
}}
QTextEdit#transBox {{ border: none; background: transparent; font-size: {FONT_SIZE['lg']}px; }}
QListWidget#recordList {{
    background: {t['surface']}; border: 1px solid {t['border']}; border-radius: {RADIUS['sm']}px;
    padding: 4px; font-size: {FONT_SIZE['md']}px; outline: none;
}}
QListWidget#recordList::item {{ padding: 6px 8px; border-radius: 6px; }}
QListWidget#recordList::item:selected {{ background: {t['accent_tint']}; color: {t['accent']}; }}
QTextEdit#phraseEditor {{
    background: {t['stripe']}; border: 1px solid {t['border']}; border-radius: {RADIUS['sm']}px;
    font-size: {FONT_SIZE['md']}px; padding: 8px;
}}
QFrame#templateCard {{
    background: {t['stripe']}; border: 1.4px dashed {t['border_strong']};
    border-radius: {RADIUS['lg']}px;
}}
QFrame#templateCard:hover {{ border: 1.4px dashed {t['accent']}; }}
QLabel#tplTitle {{ background: transparent; font-weight: 700; font-size: {FONT_SIZE['lg']}px; }}
QLabel#tplDesc {{ background: transparent; color: {t['muted']}; font-size: {FONT_SIZE['sm']}px; }}
QLabel#tplPlus {{ background: transparent; color: {t['muted']}; font-size: 20px; }}
QTextEdit#detailBox {{
    background: {t['stripe']}; border: 1px solid {t['border']}; border-radius: {RADIUS['sm']}px;
    font-size: {FONT_SIZE['md']}px; padding: 8px;
}}
QLabel#swapIcon {{ background: transparent; font-size: 18px; color: {t['muted']}; padding: 0 4px; }}
QLabel#mutedLabel {{ color: {t['text_2']}; background: transparent; }}
QLabel#hero {{ font-size: {FONT_SIZE['hero']}px; font-weight: 700; background: transparent; }}
QLabel#title {{ font-size: {FONT_SIZE['title']}px; font-weight: 700; background: transparent; }}

QPushButton {{ background: transparent; border: none; }}
QPushButton#primary {{
    background: {t['accent']}; color: white; border: none; border-radius: {RADIUS['md']}px;
    padding: 9px 16px; font-size: {FONT_SIZE['lg']}px; font-weight: 600;
}}
QPushButton#primary:hover {{ background: {t['accent_hover']}; }}
QPushButton#primary:pressed {{ background: {t['accent_press']}; }}
QPushButton#secondary {{
    background: {t['surface']}; color: {t['text']}; border: 1px solid {t['border']};
    border-radius: {RADIUS['md']}px; padding: 8px 15px; font-size: {FONT_SIZE['lg']}px;
}}
QPushButton#secondary:hover {{ border: 1px solid {t['accent']}; color: {t['accent']}; }}
QPushButton#danger {{
    background: {t['danger']}; color: white; border: none; border-radius: {RADIUS['md']}px;
    padding: 9px 16px; font-weight: 600;
}}
QPushButton#danger:hover {{ background: {t['danger_line']}; }}
QPushButton#ghost {{ background: transparent; border: none; color: {t['text_2']}; font-size: {FONT_SIZE['md']}px; }}
QPushButton#ghost:hover {{ color: {t['accent']}; }}
QPushButton#iconBtn {{ background: transparent; border: none; border-radius: {RADIUS['sm']}px; }}
QPushButton#iconBtn:hover {{ background: {t['soft']}; }}

QLineEdit, QComboBox, QSpinBox {{
    background: {t['surface']}; border: 1px solid {t['border']}; border-radius: {RADIUS['sm']}px;
    padding: 8px 12px; font-size: {FONT_SIZE['md']}px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {t['accent']}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right; width: 22px; border: none; }}
QComboBox QAbstractItemView {{ background: {t['surface']}; border: 1px solid {t['border']}; selection-background-color: {t['accent_tint']}; }}

QFrame#userBubble {{ background: {t['accent']}; border-radius: {RADIUS['lg']}px; }}
QFrame#botBubble {{ background: {t['soft']}; border-radius: {RADIUS['lg']}px; }}
QLabel#userText {{ color: white; background: transparent; font-size: {FONT_SIZE['lg']}px; }}
QLabel#botText {{ color: {t['text']}; background: transparent; font-size: {FONT_SIZE['lg']}px; }}

QFrame#sugCard {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: {RADIUS['md']}px; }}
QFrame#sugCard:hover {{ border: 1px solid {t['accent']}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px; }}
QScrollBar::handle:vertical {{ background: #c7ccd6; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------- 侧边导航 ---------- */
QWidget#sidebar {{ background: {t['side']}; border-radius: {RADIUS['xl']}px; }}
QPushButton#navItem {{
    background: transparent; border: none; border-radius: {RADIUS['md']}px;
    text-align: left; padding: 8px 14px; color: {t['side_text']}; font-size: {FONT_SIZE['lg']}px;
}}
QPushButton#navItem:hover {{ background: {t['hover']}; }}
QPushButton#navItem:checked {{ background: {t['side_active']}; font-weight: 600; }}

/* ---------- 列表行 ---------- */
QFrame#listRow {{ background: transparent; border-radius: {RADIUS['md']}px; }}
QFrame#listRow:hover {{ background: {t['soft']}; }}
QLabel#rowTitle {{ background: transparent; font-size: {FONT_SIZE['lg']}px; font-weight: 600; }}
QLabel#rowSubtitle {{ background: transparent; color: {t['muted']}; font-size: {FONT_SIZE['sm']}px; }}

/* ---------- 标签 ---------- */
QFrame#chip {{ background: {t['soft']}; border-radius: {RADIUS['pill']}px; }}
QLabel#chipText {{ background: transparent; color: {t['text_2']}; font-size: {FONT_SIZE['xs']}px; }}

/* ---------- 搜索框 ---------- */
QLineEdit#search {{
    background: {t['soft']}; border: 1px solid transparent; border-radius: {RADIUS['pill']}px;
    padding: 9px 16px; font-size: {FONT_SIZE['md']}px;
}}
QLineEdit#search:focus {{ border: 1px solid {t['accent']}; background: {t['surface']}; }}

/* ---------- AI 面板 ---------- */
QWidget#msgHolder {{ background: transparent; }}
QLabel#emptyTitle {{ background: transparent; font-size: {FONT_SIZE['xl']}px; font-weight: 700; color: {t['text']}; }}
QPushButton#chatRow {{
    background: transparent; border: none; border-radius: {RADIUS['sm']}px;
    text-align: left; padding: 8px 11px; font-size: {FONT_SIZE['md']}px;
}}
QPushButton#chatRow:hover {{ background: {t['soft']}; }}
QPushButton#chatRow[selected="true"] {{ background: {t['accent_tint']}; color: {t['accent']}; font-weight: 600; }}
QFrame#welcomeCard {{ background: {t['accent_tint']}; border-radius: {RADIUS['xl']}px; }}
QFrame#inputCard {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: {RADIUS['lg']}px; }}
QTextEdit#input {{ border: none; background: transparent; font-size: {FONT_SIZE['lg']}px; }}
QPushButton#send {{
    background: {t['accent']}; color: white; border: none; border-radius: {RADIUS['md']}px;
    font-weight: 600;
}}
QPushButton#send:hover {{ background: {t['accent_hover']}; }}
QLabel#sugTitle {{ background: transparent; font-weight: 700; font-size: {FONT_SIZE['md']}px; }}
QLabel#sugSub {{ background: transparent; color: {t['muted']}; font-size: {FONT_SIZE['sm']}px; }}

/* ---------- 弹窗 ---------- */
QFrame#modal {{ background: {t['surface']}; border-radius: {RADIUS['xl']}px; }}
QFrame#toast {{ background: {t['text']}; border-radius: {RADIUS['pill']}px; }}
QLabel#toastText {{ color: {t['surface']}; background: transparent; font-size: {FONT_SIZE['md']}px; }}
"""


def add_shadow(widget, blur: int = 24, dy: int = 6, alpha: int = 40):
    """给控件加柔和投影 (QSS 不支持 box-shadow)。"""
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, dy)
    eff.setColor(QColor(31, 45, 74, alpha))
    widget.setGraphicsEffect(eff)
