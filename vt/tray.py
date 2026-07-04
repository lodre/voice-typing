import logging

import pystray
from PIL import Image, ImageDraw

from vt import autostart, config

log = logging.getLogger("vt.tray")

_OEM_NAMES = {
    0xC0: "Ё", 0xDE: "Э", 0xBA: "Ж", 0xDB: "Х", 0xDD: "Ъ",
    0xBC: "Б", 0xBE: "Ю", 0xBF: "/", 0x20: "Пробел",
}


def _key_name(cfg: dict) -> str:
    vk = cfg["ptt_key_vk"]
    if 0x70 <= vk <= 0x87:
        name = f"F{vk - 0x6F}"
    elif 0x30 <= vk <= 0x5A:
        name = chr(vk)
    else:
        name = _OEM_NAMES.get(vk, f"vk={vk:#x}")
    mods = [m.capitalize() for m in cfg.get("ptt_modifiers", [])]
    return "+".join(mods + [name])


def _icon_image(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill=color)
    # стилизованный микрофон
    d.rounded_rectangle((26, 14, 38, 38), radius=6, fill="white")
    d.line((32, 40, 32, 48), fill="white", width=4)
    d.line((23, 48, 41, 48), fill="white", width=4)
    return img


class Tray:
    def __init__(self, cfg: dict, on_quit):
        self._cfg = cfg
        self._on_quit = on_quit
        self._states = {
            "loading": ("#9e9e9e", "Загрузка модели…"),
            "idle": ("#2e7d32", f"Готов — зажмите {_key_name(cfg)}"),
            "recording": ("#c62828", "Запись…"),
            "busy": ("#1565c0", "Распознавание…"),
            "error": ("#e65100", "Ошибка — см. voice-typing.log"),
        }
        self._state = "loading"
        self._images = {name: _icon_image(color) for name, (color, _) in self._states.items()}

        menu = pystray.Menu(
            pystray.MenuItem(lambda item: self._states[self._state][1], None, enabled=False),
            pystray.Menu.SEPARATOR,
            self._lang_item("Язык: авто (RU/EN)", "auto"),
            self._lang_item("Язык: только русский", "ru"),
            self._lang_item("Язык: только английский", "en"),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Автозапуск при входе в Windows",
                self._toggle_autostart,
                checked=lambda item: autostart.enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._quit),
        )
        self._icon = pystray.Icon(
            "voice-typing", self._images["loading"], "Голосовой ввод", menu
        )

    def _lang_item(self, title: str, code: str) -> pystray.MenuItem:
        def action(icon, item):
            self._cfg["language"] = code
            config.save(self._cfg)

        return pystray.MenuItem(
            title, action, radio=True,
            checked=lambda item, c=code: self._cfg["language"] == c,
        )

    def _toggle_autostart(self, icon, item) -> None:
        try:
            autostart.toggle()
        except Exception:
            log.exception("Не удалось переключить автозапуск")
            self.set_state("error")

    def _quit(self, icon, item) -> None:
        self._on_quit()
        self._icon.stop()

    def set_state(self, state: str) -> None:
        self._state = state
        self._icon.icon = self._images[state]
        self._icon.title = f"Голосовой ввод — {self._states[state][1]}"

    def run(self) -> None:
        self._icon.run()  # блокирует главный поток до «Выход»

    def stop(self) -> None:
        self._icon.stop()
