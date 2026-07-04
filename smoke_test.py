"""Smoke-тест распознавания: загрузка модели (CUDA → CPU fallback) + тестовый WAV.

Использование:
    python smoke_test.py [путь_к_модели] [файл.wav]
"""
import logging
import sys
import time
from pathlib import Path

from faster_whisper import decode_audio

from vt.transcriber import Transcriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else "models/faster-whisper-tiny"
    wav = sys.argv[2] if len(sys.argv) > 2 else "test_en.wav"
    cfg = {"model_path": model, "device": "auto", "compute_type": "auto", "beam_size": 5}

    transcriber = Transcriber(cfg)
    t0 = time.perf_counter()
    transcriber.load()
    print(f"Модель загружена за {time.perf_counter() - t0:.1f} с, устройство: {transcriber.device}")

    audio = decode_audio(str(Path(wav)), sampling_rate=16000)
    t0 = time.perf_counter()
    text = transcriber.transcribe(audio, "auto")
    print(f"[{time.perf_counter() - t0:.2f} с] {text}")


if __name__ == "__main__":
    main()
