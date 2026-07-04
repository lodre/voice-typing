"""Автозапуск при входе в Windows: ярлык в папке автозагрузки пользователя.

Ярлык указывает на текущее расположение программы, поэтому после переноса
папки на другой ПК достаточно заново включить галочку в меню в трее.
"""
import os
import sys
from pathlib import Path

from vt.config import base_dir

LINK_NAME = "VoiceTyping.lnk"


def _link_path() -> Path:
    startup = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup"
    return startup / LINK_NAME


def enabled() -> bool:
    return _link_path().exists()


def enable() -> None:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()  # вызывается из потока меню pystray, не из главного
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        lnk = shell.CreateShortCut(str(_link_path()))
        if getattr(sys, "frozen", False):
            lnk.TargetPath = str(Path(sys.executable))
            lnk.Arguments = ""
        else:
            # pythonw.exe — чтобы при входе в систему не всплывало окно консоли
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            lnk.TargetPath = str(pythonw)
            lnk.Arguments = f'"{base_dir() / "app.py"}"'
        lnk.WorkingDirectory = str(base_dir())
        lnk.Description = "Локальный голосовой ввод (RU/EN)"
        lnk.Save()
        del lnk, shell  # освободить COM-объекты ДО CoUninitialize
    finally:
        pythoncom.CoUninitialize()


def disable() -> None:
    _link_path().unlink(missing_ok=True)


def toggle() -> None:
    if enabled():
        disable()
    else:
        enable()
