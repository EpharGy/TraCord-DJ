"""Qt controller (v2) – minimal wiring to launch window without services yet."""
from __future__ import annotations

from PySide6 import QtCore

from ui_qt2.main_window import MainWindow


class QtController(QtCore.QObject):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        window.set_controller(self)

    # Stubs to satisfy MainWindow calls
    def handle_song_event(self, payload: dict) -> None:
        _ = payload

    def push_stats_update(self) -> None:
        pass

    def reload_song_requests(self) -> None:
        pass
