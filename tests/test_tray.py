from vt.tray import _key_name


def test_ctrl_combo():
    assert _key_name({"ptt_key_vk": 0xC0, "ptt_modifiers": ["ctrl"]}) == "Ctrl+Ё"


def test_function_key_without_modifiers():
    assert _key_name({"ptt_key_vk": 0x78, "ptt_modifiers": []}) == "F9"


def test_letter_key():
    assert _key_name({"ptt_key_vk": 0x41, "ptt_modifiers": ["ctrl", "shift"]}) == "Ctrl+Shift+A"


def test_unknown_vk_shows_hex():
    assert "0xff" in _key_name({"ptt_key_vk": 0xFF, "ptt_modifiers": []})
