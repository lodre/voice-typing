"""Скачивает модель Whisper (формат CTranslate2) в ./models/ для офлайн-работы.

Использование:
    python download_model.py                 # Systran/faster-whisper-large-v3
    python download_model.py Systran/faster-whisper-large-v3-turbo
    python download_model.py Systran/faster-whisper-small
"""
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

DEFAULT_REPO = "Systran/faster-whisper-large-v3"


def main() -> None:
    # Консоль Windows бывает в cp1251 и падает на символах вне неё
    sys.stdout.reconfigure(errors="replace")
    repo = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REPO
    target = Path(__file__).resolve().parent / "models" / repo.split("/")[-1]
    print(f"Скачиваю {repo} -> {target}")
    snapshot_download(repo, local_dir=target)
    print(f"Готово: {target}")


if __name__ == "__main__":
    main()
