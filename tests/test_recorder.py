import numpy as np

from vt.recorder import TARGET_RATE, Recorder


def test_stop_without_start_returns_empty():
    audio = Recorder().stop()
    assert audio.dtype == np.float32
    assert len(audio) == 0


def test_16k_passthrough():
    rec = Recorder()
    rec._rate = TARGET_RATE
    rec._chunks = [np.ones((1600, 1), dtype=np.float32)]
    audio = rec.stop()
    assert len(audio) == 1600
    assert audio.dtype == np.float32


def test_48k_resampled_to_16k():
    rec = Recorder()
    rec._rate = 48000
    rec._chunks = [np.ones((4800, 1), dtype=np.float32)]
    audio = rec.stop()
    assert len(audio) == 1600
    assert audio.dtype == np.float32
    # ресемплинг константы остаётся около той же амплитуды (без краёв)
    assert abs(float(audio[200:-200].mean()) - 1.0) < 0.05


def test_max_seconds_caps_buffer():
    rec = Recorder(max_seconds=0.1)
    rec._rate = TARGET_RATE
    chunk = np.zeros((1600, 1), dtype=np.float32)  # 0.1 с
    rec._on_audio(chunk, 1600, None, None)
    rec._on_audio(chunk, 1600, None, None)  # уже сверх лимита — отбрасывается
    assert len(rec._chunks) == 1
