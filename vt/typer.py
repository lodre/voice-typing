import logging
import time

import win32clipboard
import win32con
from pynput.keyboard import Controller, Key, KeyCode

log = logging.getLogger("vt.typer")

_kb = Controller()
VK_V = 0x56  # физическая позиция клавиши V — Ctrl+V работает в любой раскладке


def insert(text: str, cfg: dict) -> None:
    if not text:
        return
    if cfg["paste_method"] == "type_unicode":
        # SendInput с KEYEVENTF_UNICODE — не зависит от раскладки, но медленнее
        # и в отдельных приложениях глотается; это запасной режим
        _kb.type(text)
        return

    old = _get_text()
    _set_text(text)
    time.sleep(0.10)  # приложению нужно время увидеть новое содержимое буфера
    _kb.press(Key.ctrl)
    _kb.press(KeyCode.from_vk(VK_V))
    _kb.release(KeyCode.from_vk(VK_V))
    _kb.release(Key.ctrl)
    if cfg["restore_clipboard"] and old is not None:
        time.sleep(0.30)  # восстановить раньше — вставится старое содержимое
        _set_text(old)


def _open_retry(tries: int = 10, delay: float = 0.05) -> bool:
    # Буфер обмена может держать другой процесс (менеджеры буфера и т.п.)
    for _ in range(tries):
        try:
            win32clipboard.OpenClipboard()
            return True
        except Exception:
            time.sleep(delay)
    return False


def _get_text():
    if not _open_retry():
        return None
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        return None
    finally:
        win32clipboard.CloseClipboard()


def _set_text(text: str) -> None:
    if not _open_retry():
        raise RuntimeError("Не удалось открыть буфер обмена")
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()
