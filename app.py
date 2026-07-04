import logging
import os
import queue
import sys
import threading

# ctranslate2 и onnxruntime тянут каждый свой OpenMP — без этого флага
# в PyInstaller-сборке дублирующиеся libiomp/libomp роняют процесс
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import win32api
import win32event
import winerror

from vt import config, sounds, typer
from vt.config import base_dir
from vt.hotkey import PttListener
from vt.recorder import Recorder
from vt.transcriber import Transcriber
from vt.tray import Tray

log = logging.getLogger("vt.app")

TARGET_RATE = 16000


def _setup_logging() -> None:
    handlers = [logging.FileHandler(base_dir() / "voice-typing.log", encoding="utf-8")]
    if sys.stderr is not None:  # под pythonw.exe консоли нет
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=handlers,
    )


def main() -> None:
    _setup_logging()  # до чтения конфига: ошибки config.json должны попасть в лог
    cfg = config.load()

    # хэндл держим в переменной до конца main(), иначе GC закроет мьютекс
    mutex = win32event.CreateMutex(None, False, "voice-typing-single-instance")
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        log.error("Программа уже запущена — второй экземпляр не нужен")
        return

    commands: queue.Queue[str] = queue.Queue()
    model_ready = threading.Event()
    quitting = threading.Event()

    transcriber = Transcriber(cfg)
    recorder = Recorder(cfg["input_device"], cfg["max_record_seconds"])
    tray = Tray(cfg, on_quit=lambda: (quitting.set(), commands.put("quit")))

    def load_model() -> None:
        try:
            transcriber.load()
            model_ready.set()
            if not quitting.is_set():
                tray.set_state("idle")
        except Exception:
            log.exception("Модель не загрузилась")
            tray.set_state("error")
            if cfg["beep"]:
                sounds.error()

    def worker() -> None:
        recording = False
        while True:
            cmd = commands.get()
            if cmd == "quit":
                return
            if cmd == "press" and not recording:
                if not model_ready.is_set():
                    if cfg["beep"]:
                        sounds.error()
                    continue
                try:
                    recorder.start()
                except Exception:
                    log.exception("Не удалось открыть микрофон")
                    tray.set_state("error")
                    if cfg["beep"]:
                        sounds.error()
                    continue
                recording = True
                tray.set_state("recording")
                if cfg["beep"]:
                    sounds.record_start()
            elif cmd == "release" and recording:
                recording = False
                audio = recorder.stop()
                if cfg["beep"]:
                    sounds.record_stop()
                if len(audio) < cfg["min_record_seconds"] * TARGET_RATE:
                    tray.set_state("idle")
                    continue
                tray.set_state("busy")
                try:
                    text = transcriber.transcribe(audio, cfg["language"])
                    if text:
                        typer.insert(text, cfg)
                except Exception:
                    log.exception("Ошибка распознавания или вставки")
                    if cfg["beep"]:
                        sounds.error()
                tray.set_state("idle")

    threading.Thread(target=load_model, daemon=True, name="model-loader").start()
    threading.Thread(target=worker, daemon=True, name="worker").start()

    listener = PttListener(
        cfg["ptt_key_vk"],
        cfg.get("ptt_modifiers", []),
        on_press=lambda: commands.put("press"),
        on_release=lambda: commands.put("release"),
    )
    listener.start()
    log.info(
        "Запущено. Push-to-talk: %s+vk=%#x, язык: %s",
        "+".join(cfg.get("ptt_modifiers", [])) or "без модификаторов",
        cfg["ptt_key_vk"], cfg["language"],
    )

    try:
        tray.run()
    finally:
        quitting.set()
        commands.put("quit")
        listener.stop()


if __name__ == "__main__":
    main()
