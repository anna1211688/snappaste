# -*- mode: python ; coding: utf-8 -*-
"""KIVO Qt Windows onefile 打包配置。

分发形态与历史发布一致：单个 KIVO.exe + KIVO-Setup 安装包。
延迟/动态导入的后端经显式收集；OCR 在 Qt 版尚未接线，不引入无用引擎。
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('pystray')
hiddenimports += collect_submodules('yt_dlp')
hiddenimports += collect_submodules('PIL')
hiddenimports += ['qrcode', 'zoneinfo', 'tzdata', 'keyboard']

datas = collect_data_files('tzdata')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', '_tkinter', 'tkinter.ttk'],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KIVO',
    icon='KIVO.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
