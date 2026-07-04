import ctypes
import logging
import os
import sys
import sysconfig
import time
from pathlib import Path

import numpy as np

from vt.config import base_dir

log = logging.getLogger("vt.transcriber")

# Параметры VAD для коротких push-to-talk фраз; главная задача —
# подавить галлюцинации Whisper на тишине и шуме
VAD_PARAMS = dict(min_silence_duration_ms=500, speech_pad_ms=400)


def _add_cuda_dll_dirs() -> None:
    """DLL-и cuBLAS/cuDNN из pip-пакетов nvidia-* сами в PATH не попадают."""
    if getattr(sys, "frozen", False):
        nvidia_root = Path(getattr(sys, "_MEIPASS", ".")) / "nvidia"
    else:
        nvidia_root = Path(sysconfig.get_paths()["purelib"]) / "nvidia"
    if not nvidia_root.is_dir():
        return
    for bin_dir in nvidia_root.glob("*/bin"):
        os.add_dll_directory(str(bin_dir))
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def _ascii_safe_path(path: Path) -> str:
    """CTranslate2 может не открыть не-ASCII путь (например, с «Прочее») —
    подставляем короткое 8.3-имя, оно всегда ASCII, если включено на томе."""
    s = str(path)
    try:
        s.encode("ascii")
        return s
    except UnicodeEncodeError:
        pass
    buf = ctypes.create_unicode_buffer(2048)
    n = ctypes.windll.kernel32.GetShortPathNameW(s, buf, 2048)
    if 0 < n < 2048:
        try:
            buf.value.encode("ascii")
            return buf.value
        except UnicodeEncodeError:
            pass
    return s


class Transcriber:
    def __init__(self, cfg: dict):
        self._cfg = cfg
        self._model = None
        self.device = None

    def load(self) -> None:
        _add_cuda_dll_dirs()
        from faster_whisper import WhisperModel  # тяжёлый импорт — держим вне главного потока

        model_path = Path(self._cfg["model_path"])
        if not model_path.is_absolute():
            model_path = base_dir() / model_path
        if not model_path.is_dir():
            raise RuntimeError(
                f"Модель не найдена: {model_path}\nСкачайте её: python download_model.py"
            )
        path = _ascii_safe_path(model_path)

        if self._cfg["device"] == "auto":
            candidates = [("cuda", "float16"), ("cpu", "int8")]
        else:
            ct = self._cfg["compute_type"]
            if ct == "auto":
                ct = "float16" if self._cfg["device"] == "cuda" else "int8"
            candidates = [(self._cfg["device"], ct)]

        last_err = None
        for device, compute_type in candidates:
            try:
                model = WhisperModel(path, device=device, compute_type=compute_type)
                # Прогрев на секунде тишины: отсутствие CUDA-ядер под нашу видеокарту
                # всплывает здесь, при старте, а не на первой продиктованной фразе
                segments, _ = model.transcribe(
                    np.zeros(16000, dtype=np.float32), beam_size=1, vad_filter=False
                )
                list(segments)
            except Exception as e:
                last_err = e
                log.warning("Не удалось загрузить на %s/%s: %s", device, compute_type, e)
                continue
            self._model = model
            self.device = device
            log.info("Модель загружена: %s (%s, %s)", path, device, compute_type)
            return
        raise RuntimeError(f"Модель не загрузилась ни на одном устройстве: {last_err}")

    def transcribe(self, audio: np.ndarray, language: str) -> str:
        t0 = time.perf_counter()
        segments, info = self._model.transcribe(
            audio,
            language=None if language == "auto" else language,
            beam_size=self._cfg["beam_size"],
            vad_filter=True,
            vad_parameters=VAD_PARAMS,
            condition_on_previous_text=False,
        )
        text = "".join(s.text for s in segments).strip()
        log.info(
            "аудио %.1f с -> распознано за %.2f с [%s] %r",
            len(audio) / 16000, time.perf_counter() - t0, info.language, text[:100],
        )
        return text
