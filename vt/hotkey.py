from pynput import keyboard

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
_DOWN = (WM_KEYDOWN, WM_SYSKEYDOWN)
_UP = (WM_KEYUP, WM_SYSKEYUP)

# vk-коды левой/правой клавиши каждого модификатора
MODIFIER_VKS = {
    "ctrl": (0xA2, 0xA3),
    "alt": (0xA4, 0xA5),
    "shift": (0xA0, 0xA1),
    "win": (0x5B, 0x5C),
}


class PttListener:
    """Глобальный push-to-talk: (модификаторы+)клавиша по vk-кодам,
    одинаковым в русской и английской раскладках.

    Логика живёт в win32_event_filter: он видит события раньше приложений
    и умеет глотать их (suppress_event), чтобы сочетание не срабатывало
    в активном окне (например, не открывало терминал в VS Code).
    Фильтр обязан быть лёгким: при задержке >300 мс (LowLevelHooksTimeout)
    Windows молча снимает клавиатурный хук.
    """

    def __init__(self, vk: int, modifiers, on_press, on_release):
        self._target_vk = vk
        self._mod_groups = [MODIFIER_VKS[name] for name in modifiers]
        self._on_press = on_press
        self._on_release = on_release
        self._mods_down = set()
        self._down = False  # заодно давит автоповтор зажатой клавиши
        self._listener = keyboard.Listener(win32_event_filter=self._filter)

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()

    def _mods_ok(self) -> bool:
        return all(
            any(vk in self._mods_down for vk in group) for group in self._mod_groups
        )

    def _filter(self, msg, data) -> bool:
        vk = data.vkCode
        if any(vk in group for group in self._mod_groups):
            if msg in _DOWN:
                self._mods_down.add(vk)
            elif msg in _UP:
                self._mods_down.discard(vk)
            return True  # сами модификаторы приложениям не мешают — пропускаем
        if vk != self._target_vk:
            return True
        if msg in _DOWN:
            if self._down:
                # автоповтор зажатой клавиши — глотаем; suppress_event() бросает
                # исключение, дальше фильтр не выполняется
                self._listener.suppress_event()
            elif self._mods_ok():
                self._down = True
                self._on_press()
                self._listener.suppress_event()
        elif msg in _UP and self._down:
            # отпускание главной клавиши завершает запись, даже если Ctrl уже отпущен
            self._down = False
            self._on_release()
            self._listener.suppress_event()
        return True
