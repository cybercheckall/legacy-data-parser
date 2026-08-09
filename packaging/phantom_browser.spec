# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Find QtWebEngine resources path
import PyQt6
pyqt6_path = os.path.dirname(PyQt6.__file__)
qt6_path = os.path.join(pyqt6_path, 'Qt6')

# Collect QtWebEngine data files and icon assets
datas = [
    ('owl_icon.jpg', '.'),
    ('owl_icon.ico', '.'),
    ('owl_icon.png', '.'),
]
web_engine_resources = os.path.join(qt6_path, 'resources')
if os.path.isdir(web_engine_resources):
    for f in os.listdir(web_engine_resources):
        src = os.path.join(web_engine_resources, f)
        if os.path.isfile(src):
            datas.append((src, 'PyQt6/Qt6/resources'))

# Include QtWebEngineProcess executable
web_engine_process = os.path.join(qt6_path, 'bin', 'QtWebEngineProcess.exe')
if os.path.isfile(web_engine_process):
    datas.append((web_engine_process, 'PyQt6/Qt6/bin'))

# Include translations
translations_dir = os.path.join(qt6_path, 'translations')
if os.path.isdir(translations_dir):
    for f in os.listdir(translations_dir):
        if f.startswith('qtwebengine'):
            src = os.path.join(translations_dir, f)
            if os.path.isfile(src):
                datas.append((src, 'PyQt6/Qt6/translations'))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebChannel',
        'PyQt6.QtNetwork',
        'PyQt6.QtPositioning',
        'pynput.keyboard._win32',
        'pynput._util.win32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'tensorboard', 'keras',
        'matplotlib', 'pandas', 'scipy', 'sympy',
        'nltk', 'numba', 'llvmlite',
        'IPython', 'jedi', 'sqlite3', 'tkinter',
        'faster_whisper', 'whisper', 'sounddevice',
        'pyarrow', 'sklearn', 'librosa',
        'PySide6', 'PySide2', 'PyQt5',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Owl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='owl_icon.ico',
)
