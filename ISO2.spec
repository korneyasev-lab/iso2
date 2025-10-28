# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ISO2
Компиляция: pyinstaller ISO2.spec
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'config',
        'logic',
        'gui_main',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ISO2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Без консольного окна
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
    upx=True,
    upx_exclude=[],
    name='ISO2',
)

app = BUNDLE(
    coll,
    name='ISO2.app',
    icon=None,  # Можно добавить путь к .icns файлу
    bundle_identifier='com.iso2.app',
    info_plist={
        'CFBundleName': 'ISO2',
        'CFBundleDisplayName': 'ISO2 - Управление документацией СМК',
        'CFBundleGetInfoString': 'Система управления документацией СМК',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSHumanReadableCopyright': '© 2025 ISO2',
    },
)
