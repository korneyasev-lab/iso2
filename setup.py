"""
Setup script for creating macOS .app bundle using py2app
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['tkinter', 'openpyxl'],
    'includes': [
        'config',
        'logic',
        'gui_main',
        'registry',
        'employees'
    ],
    'iconfile': None,  # Можно добавить путь к иконке .icns если есть
    'plist': {
        'CFBundleName': 'ISO2',
        'CFBundleDisplayName': 'ISO2 - Управление документацией СМК',
        'CFBundleGetInfoString': 'Система управления документацией СМК',
        'CFBundleIdentifier': 'com.iso2.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': '© 2025 ISO2'
    },
    # Отключаем автоматическую подпись кода (решает проблему RuntimeError)
    'no_chdir': True,
    'strip': False
}

setup(
    name='ISO2',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
