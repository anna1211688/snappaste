# -*- mode: python ; coding: utf-8 -*-
"""KIVO PyInstaller 打包配置。

当前为 onedir 形态（构建快、便于排查依赖）；onefile/onedir 形态待用户拍板，
切换 onefile 只需把 EXE 的二进制并入并去掉 COLLECT。

延迟/动态导入的包（pystray 后端、yt_dlp 提取器、PIL 插件等）经
collect_submodules 显式收集，避免运行时 ModuleNotFoundError。
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = []
# 平台后端在运行时按系统动态选择, 全部收集（在哪个平台构建就只收得到哪个）
hiddenimports += collect_submodules('pystray')
# yt_dlp 经 lazy loader 加载大量 extractor, 静态分析会漏
hiddenimports += collect_submodules('yt_dlp')
# PIL 插件按需动态发现
hiddenimports += collect_submodules('PIL')
# 显式延迟导入
hiddenimports += ['qrcode', 'zoneinfo', 'tzdata']
# Windows 全局热键（仅 Windows 构建时存在, 其他平台自动跳过）
hiddenimports += ['keyboard']

# 时区数据库（zoneinfo 运行时读取）
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
    # 已全面迁移到 PySide6, 排除 Tkinter 减重
    excludes=['tkinter', '_tkinter', 'tkinter.ttk'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KIVO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI 应用, 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='KIVO',
)
