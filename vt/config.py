import json
import logging
import sys
from pathlib import Path

log = logging.getLogger("vt.config")

DEFAULTS = {
    "ptt_key_vk": 0xC0,          # Ё/` — vk-код не зависит от раскладки RU/EN
    "ptt_modifiers": ["ctrl"],   # зажимать вместе с клавишей; [] = клавиша сама по себе
    "language": "auto",           # auto | ru | en
    "model_path": "models/faster-whisper-large-v3",
    "device": "auto",             # auto | cuda | cpu
    "compute_type": "auto",       # auto: float16 на cuda, int8 на cpu
    "paste_method": "clipboard",  # clipboard | type_unicode
    "restore_clipboard": True,
    "beam_size": 5,
    "input_device": None,         # None = микрофон по умолчанию (имя или индекс sounddevice)
    "min_record_seconds": 0.3,
    "max_record_seconds": 600,
    "beep": True,
}


def base_dir() -> Path:
    # В PyInstaller-сборке config.json и models/ лежат рядом с exe, а не в _internal
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def config_path() -> Path:
    return base_dir() / "config.json"


def load() -> dict:
    cfg = dict(DEFAULTS)
    path = config_path()
    if path.exists():
        try:
            # utf-8-sig: некоторые редакторы сохраняют JSON с BOM
            with open(path, encoding="utf-8-sig") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError(f"ожидался JSON-объект, получен {type(data).__name__}")
            cfg.update(data)
        except (json.JSONDecodeError, OSError, ValueError):
            # опечатка в правленном вручную config.json не должна молча ронять
            # автозапуск; сам файл не перезаписываем — пусть его починят
            log.exception("config.json не читается — работаю с настройками по умолчанию")
    else:
        save(cfg)
    return cfg


def save(cfg: dict) -> None:
    with open(config_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
