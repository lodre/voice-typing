import threading
import winsound


def _beep(freq: int, ms: int) -> None:
    # winsound.Beep блокирует поток, поэтому играем из фонового
    threading.Thread(target=winsound.Beep, args=(freq, ms), daemon=True).start()


def record_start() -> None:
    _beep(880, 120)


def record_stop() -> None:
    _beep(600, 120)


def error() -> None:
    _beep(300, 350)
