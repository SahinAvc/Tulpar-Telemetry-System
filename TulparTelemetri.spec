# -*- mode: python ; coding: utf-8 -*-
"""
TULPAR TELEMETRI - PyInstaller spec

Windows'ta  .exe, Mac'te .app uretir. Django'nun template, migration ve
gizli importlarini pakete gomer.

Derleme:
    pip install pyinstaller
    pyinstaller TulparTelemetri.spec

Cikti:
    dist/TulparTelemetri.exe   (Windows)
    dist/TulparTelemetri.app   (Mac)
"""

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

blok_cipher = None

# --- Django'nun otomatik bulamadigi gizli importlar ---
gizli_importlar = []
gizli_importlar += collect_submodules("django")
gizli_importlar += collect_submodules("channels")
gizli_importlar += collect_submodules("daphne")
gizli_importlar += collect_submodules("rest_framework")
gizli_importlar += collect_submodules("serial")
gizli_importlar += collect_submodules("asgiref")
gizli_importlar += collect_submodules("twisted")
gizli_importlar += collect_submodules("autobahn")
gizli_importlar += [
    "telemetri",
    "telemetri.apps",
    "telemetri.consumers",
    "telemetri.routing",
    "telemetri.urls",
    "telemetri.views",
    "telemetri.utils",
    "telemetri.models",
    "telemetri.serializers",
    "telemetri.management.commands.lora_dinle",
    "izleme.settings",
    "izleme.asgi",
    "izleme.urls",
]

# --- Pakete gomulecek veri dosyalari (template, migration) ---
veri_dosyalari = [
    ("templates", "templates"),
    ("telemetri/migrations", "telemetri/migrations"),
]
veri_dosyalari += collect_data_files("rest_framework")
# autobahn/twisted paketlerinin ic veri dosyalari (.c, .pem vb.)
veri_dosyalari += collect_data_files("autobahn")
veri_dosyalari += collect_data_files("twisted")

a = Analysis(
    ["app.py"],
    pathex=[os.getcwd()],
    binaries=[],
    datas=veri_dosyalari,
    hiddenimports=gizli_importlar,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],   # gerekmiyorsa boyutu kucultur
    cipher=blok_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=blok_cipher)

# ── Windows: tek dosya .exe / Mac: .app paketi ───────────────────────────────
# Windows'ta tek .exe uretir. Mac'te .app bundle uretir (onedir gerekir).
import sys as _sys

if _sys.platform == "darwin":
    # --- MAC: onedir + .app bundle ---
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="TulparTelemetri",
        debug=False,
        strip=False,
        upx=True,
        console=False,
        icon=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name="TulparTelemetri",
    )
    app = BUNDLE(
        coll,
        name="TulparTelemetri.app",
        icon=None,
        bundle_identifier="com.tulpar.telemetri",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
        },
    )
else:
    # --- WINDOWS / LINUX: tek dosya .exe ---
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name="TulparTelemetri",
        debug=False,
        strip=False,
        upx=True,
        console=False,      # pencereli - siyah terminal cikmaz
        icon=None,          # ikon.ico eklemek istersen buraya yaz
    )
