import logging

import numpy as np
import sounddevice as sd

log = logging.getLogger("vt.recorder")

TARGET_RATE = 16000  # Whisper принимает только 16 кГц


class Recorder:
    """Пишет микрофон в память: start() ... stop() -> float32 моно 16 кГц."""

    def __init__(self, input_device=None, max_seconds: float = 600):
        self._device = input_device
        self._max_seconds = max_seconds
        self._stream = None
        self._chunks = []
        self._samples = 0
        self._rate = TARGET_RATE

    def start(self) -> None:
        self._chunks = []
        self._samples = 0
        try:
            self._stream = self._open(TARGET_RATE)
        except sd.PortAudioError:
            # Часть устройств/WASAPI не открывается на 16 кГц — пишем на 48 и ресемплим
            log.info("Микрофон не открылся на 16 кГц, пробую 48 кГц")
            self._stream = self._open(48000)
        self._stream.start()

    def _open(self, rate: int) -> sd.InputStream:
        self._rate = rate
        return sd.InputStream(
            samplerate=rate,
            channels=1,
            dtype="float32",
            device=self._device,
            callback=self._on_audio,
        )

    def _on_audio(self, indata, frames, time_info, status) -> None:
        if status:
            log.warning("Аудиопоток: %s", status)
        if self._samples >= self._max_seconds * self._rate:
            return  # защита от бесконечно зажатой клавиши
        self._chunks.append(indata.copy())
        self._samples += frames

    def stop(self) -> np.ndarray:
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()
            stream.close()
        if not self._chunks:
            return np.zeros(0, dtype=np.float32)
        audio = np.concatenate(self._chunks)[:, 0]
        if self._rate != TARGET_RATE:
            from scipy.signal import resample_poly

            audio = resample_poly(audio, TARGET_RATE, self._rate).astype(np.float32)
        return audio
