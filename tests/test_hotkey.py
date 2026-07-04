import pytest

from vt.hotkey import WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP, PttListener

VK_TARGET = 0xC0
VK_LCTRL = 0xA2
VK_RCTRL = 0xA3


class _Suppressed(Exception):
    pass


class _FakeInnerListener:
    def suppress_event(self):
        raise _Suppressed()


class _Data:
    def __init__(self, vk):
        self.vkCode = vk


def make(modifiers=("ctrl",), vk=VK_TARGET):
    presses, releases = [], []
    ptt = PttListener(
        vk, list(modifiers),
        on_press=lambda: presses.append(1),
        on_release=lambda: releases.append(1),
    )
    ptt._listener = _FakeInnerListener()
    return ptt, presses, releases


def feed(ptt, msg, vk):
    """Прогоняет событие через фильтр; True = событие подавлено."""
    try:
        ptt._filter(msg, _Data(vk))
        return False
    except _Suppressed:
        return True


def test_target_without_modifier_passes_through():
    ptt, presses, _ = make()
    assert not feed(ptt, WM_KEYDOWN, VK_TARGET)  # обычное «ё» уходит в приложение
    assert presses == []


def test_chord_starts_and_release_stops():
    ptt, presses, releases = make()
    assert not feed(ptt, WM_KEYDOWN, VK_LCTRL)  # ctrl приложениям не мешает
    assert feed(ptt, WM_KEYDOWN, VK_TARGET)
    assert presses == [1]
    assert feed(ptt, WM_KEYUP, VK_TARGET)
    assert releases == [1]


def test_autorepeat_fires_press_once():
    ptt, presses, _ = make()
    feed(ptt, WM_KEYDOWN, VK_LCTRL)
    for _ in range(5):
        assert feed(ptt, WM_KEYDOWN, VK_TARGET)  # каждый автоповтор подавлен
    assert presses == [1]


def test_release_without_press_passes_through():
    ptt, _, releases = make()
    assert not feed(ptt, WM_KEYUP, VK_TARGET)
    assert releases == []


def test_ctrl_released_before_target_still_stops():
    ptt, presses, releases = make()
    feed(ptt, WM_KEYDOWN, VK_LCTRL)
    feed(ptt, WM_KEYDOWN, VK_TARGET)
    feed(ptt, WM_KEYUP, VK_LCTRL)
    assert feed(ptt, WM_KEYUP, VK_TARGET)
    assert presses == [1] and releases == [1]


def test_right_ctrl_counts_as_modifier():
    ptt, presses, _ = make()
    feed(ptt, WM_SYSKEYDOWN, VK_RCTRL)
    assert feed(ptt, WM_SYSKEYDOWN, VK_TARGET)
    assert presses == [1]


def test_no_modifiers_config_triggers_on_bare_key():
    ptt, presses, releases = make(modifiers=(), vk=0x78)  # F9
    assert feed(ptt, WM_KEYDOWN, 0x78)
    assert feed(ptt, WM_KEYUP, 0x78)
    assert presses == [1] and releases == [1]
