# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

project_dir = os.path.abspath(".")
icon_path = os.path.join(project_dir, "image.ico")
datas = [(os.path.join(project_dir, "ffmpeg"), "ffmpeg")]
datas += [(icon_path, ".")]
datas += collect_data_files("customtkinter")
datas += collect_data_files("tkinterdnd2")

a = Analysis(
    ["main.py"],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=["sounddevice", "tkinterdnd2"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="MP3Normalizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    exclude_binaries=True,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="MP3Normalizer",
)
