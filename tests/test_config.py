import json

import pytest

import vt.config as config


@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "base_dir", lambda: tmp_path)
    return tmp_path


def test_missing_file_creates_defaults(base):
    cfg = config.load()
    assert cfg == config.DEFAULTS
    assert (base / "config.json").exists()


def test_user_values_override_defaults(base):
    (base / "config.json").write_text('{"language": "ru"}', encoding="utf-8")
    cfg = config.load()
    assert cfg["language"] == "ru"
    assert cfg["ptt_key_vk"] == config.DEFAULTS["ptt_key_vk"]


def test_broken_json_falls_back_and_keeps_file(base):
    (base / "config.json").write_text("{ broken", encoding="utf-8")
    cfg = config.load()
    assert cfg == config.DEFAULTS
    # файл пользователя не перезаписывается настройками по умолчанию
    assert (base / "config.json").read_text(encoding="utf-8") == "{ broken"


def test_json_with_bom(base):
    (base / "config.json").write_text('{"language": "en"}', encoding="utf-8-sig")
    assert config.load()["language"] == "en"


def test_non_dict_json_falls_back(base):
    (base / "config.json").write_text("[1, 2, 3]", encoding="utf-8")
    assert config.load() == config.DEFAULTS


def test_save_load_roundtrip(base):
    cfg = dict(config.DEFAULTS, language="ru", beep=False)
    config.save(cfg)
    assert config.load() == cfg
    # файл — валидный JSON без ASCII-эскейпов
    raw = (base / "config.json").read_text(encoding="utf-8")
    assert json.loads(raw)["language"] == "ru"
