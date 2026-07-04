from pathlib import Path

from vt.transcriber import _ascii_safe_path


def test_ascii_path_unchanged(tmp_path):
    assert _ascii_safe_path(tmp_path) == str(tmp_path)


def test_cyrillic_path_resolves_to_existing(tmp_path):
    p = tmp_path / "модели"
    p.mkdir()
    result = _ascii_safe_path(p)
    # короткое 8.3-имя может быть выключено на томе — тогда путь остаётся как есть;
    # главное, что результат указывает на ту же существующую папку
    assert Path(result).exists()
    assert Path(result).samefile(p)
