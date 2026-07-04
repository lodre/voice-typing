# -*- mode: python ; coding: utf-8 -*-
"""Сборка переносимой папки: pyinstaller VoiceTyping.spec

Модель и config.json в сборку не входят — они лежат РЯДОМ с exe
(см. vt.config.base_dir), их копирует build.ps1.
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

# site-packages того окружения, из которого запущен PyInstaller
site = Path(sys.prefix) / "Lib" / "site-packages"

# CUDA-библиотеки из pip-пакетов nvidia-*: складываем в _internal/nvidia/<имя>/bin,
# где их ищет vt.transcriber._add_cuda_dll_dirs; на ПК без NVIDIA они просто не нужны
nvidia_bins = [
    (str(dll), f"nvidia/{sub}/bin")
    for sub in ("cublas", "cudnn", "cuda_nvrtc")
    for dll in (site / "nvidia" / sub / "bin").glob("*.dll")
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=nvidia_bins,
    # ассеты faster-whisper (silero_vad_*.onnx) — без них vad_filter падает
    datas=collect_data_files("faster_whisper"),
    hiddenimports=["win32com", "win32com.client", "pythoncom", "win32timezone"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="VoiceTyping",
    icon="icon.ico",
    console=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="VoiceTyping",
    upx=False,
)
