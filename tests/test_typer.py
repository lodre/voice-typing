import pytest

import vt.typer as typer


class _KbSpy:
    def __init__(self):
        self.typed = []
        self.keys = []

    def type(self, text):
        self.typed.append(text)

    def press(self, key):
        self.keys.append(("press", key))

    def release(self, key):
        self.keys.append(("release", key))


@pytest.fixture
def spy(monkeypatch):
    kb = _KbSpy()
    clipboard = {"value": "старое", "sets": []}

    def fake_get():
        return clipboard["value"]

    def fake_set(text):
        clipboard["sets"].append(text)
        clipboard["value"] = text

    monkeypatch.setattr(typer, "_kb", kb)
    monkeypatch.setattr(typer, "_get_text", fake_get)
    monkeypatch.setattr(typer, "_set_text", fake_set)
    monkeypatch.setattr(typer.time, "sleep", lambda s: None)
    return kb, clipboard


def test_empty_text_does_nothing(spy):
    kb, clipboard = spy
    typer.insert("", {"paste_method": "clipboard", "restore_clipboard": True})
    assert kb.keys == [] and kb.typed == [] and clipboard["sets"] == []


def test_type_unicode_bypasses_clipboard(spy):
    kb, clipboard = spy
    typer.insert("привет", {"paste_method": "type_unicode"})
    assert kb.typed == ["привет"]
    assert clipboard["sets"] == []


def test_clipboard_paste_and_restore(spy):
    kb, clipboard = spy
    typer.insert("текст", {"paste_method": "clipboard", "restore_clipboard": True})
    # положили новый текст, после вставки вернули старый
    assert clipboard["sets"] == ["текст", "старое"]
    # Ctrl+V нажат и отпущен
    assert [a for a, _ in kb.keys] == ["press", "press", "release", "release"]


def test_clipboard_without_restore(spy):
    kb, clipboard = spy
    typer.insert("текст", {"paste_method": "clipboard", "restore_clipboard": False})
    assert clipboard["sets"] == ["текст"]


def test_no_restore_when_old_clipboard_empty(spy, monkeypatch):
    kb, clipboard = spy
    monkeypatch.setattr(typer, "_get_text", lambda: None)
    typer.insert("текст", {"paste_method": "clipboard", "restore_clipboard": True})
    assert clipboard["sets"] == ["текст"]
