# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

SEED = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(Path(SPECPATH) / "CitizenSetup.py")],
    pathex=[str(SEED)],
    binaries=[],
    datas=[(str(SEED), "citizen-seed")],
    hiddenimports=["citizen_seed"],
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
    a.binaries,
    a.datas,
    [],
    name="CitizenSetup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
