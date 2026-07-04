from pathlib import Path

from vt.transcriber import _ascii_safe_path


def test_ascii_path_unchanged():
    # ASCII-ветка возвращает строку сразу, не трогая диск, поэтому путь
    # может не существовать; литерал не зависит от расположения temp pytest
    assert _ascii_safe_path(Path(r"C:\Temp\models")) == r"C:\Temp\models"


def test_cyrillic_path_resolves_to_existing(tmp_path):
    p = tmp_path / "модели"
    p.mkdir()
    result = _ascii_safe_path(p)
    # короткое 8.3-имя может быть выключено на томе — тогда путь остаётся как есть;
    # главное, что результат указывает на ту же существующую папку
    assert Path(result).exists()
    assert Path(result).samefile(p)
