# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building Owl.app on macOS."""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
project_root = Path(SPECPATH).resolve().parent

brand = project_root / "assets" / "brand"
datas = [
    (str(brand / "owl_icon.png"), "."),
    (str(brand / "owl_icon.jpg"), "."),
    (str(brand / "owl_icon.ico"), "."),
    (str(brand / "owl_icon.icns"), "."),
    (str(brand / "owl-.svg"), "."),
]
binaries = []
hiddenimports = [
    "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtWebEngineCore",
    "PyQt6.QtWebChannel",
    "PyQt6.QtNetwork",
    "PyQt6.QtPositioning",
    "PyQt6.QtPrintSupport",
]

# Pull in QtWebEngine frameworks, Helpers/QtWebEngineProcess.app, resources, locales
for package in ("PyQt6", "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        pass

icon_path = brand / "owl_icon.icns"
if not icon_path.exists():
    icon_path = brand / "owl_icon.png"

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch",
        "torchvision",
        "torchaudio",
        "tensorflow",
        "tensorboard",
        "keras",
        "matplotlib",
        "pandas",
        "scipy",
        "sympy",
        "nltk",
        "numba",
        "llvmlite",
        "IPython",
        "jedi",
        "tkinter",
        "PySide6",
        "PySide2",
        "PyQt5",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Owl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Owl",
)

app = BUNDLE(
    coll,
    name="Owl.app",
    icon=str(icon_path),
    bundle_identifier="com.owl.stealthbrowser",
    info_plist={
        "CFBundleName": "Owl",
        "CFBundleDisplayName": "Owl",
        "CFBundleShortVersionString": "2.0.0",
        "CFBundleVersion": "2.0.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "12.0",
        "NSPrincipalClass": "NSApplication",
        "NSAppleEventsUsageDescription": "Owl may use system events for window management.",
    },
)
