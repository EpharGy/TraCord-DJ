"""Qt signal bridge for the domain event bus (v2)."""
from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6 import QtCore

from tracord.core.events import EventTopic, subscribe_event


class QtEventHub(QtCore.QObject):
    songPlayed = QtCore.Signal(dict)
    # Accept None payloads for stats updates
    statsUpdated = QtCore.Signal(object)
    songRequestAdded = QtCore.Signal(object)
    songRequestDeleted = QtCore.Signal(object)
    logMessage = QtCore.Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._subs: list[Callable[[], None]] = []
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._subs.extend(
            [
                subscribe_event(EventTopic.SONG_PLAYED, self._emit(self.songPlayed)),
                subscribe_event(EventTopic.STATS_UPDATED, self._emit(self.statsUpdated)),
                subscribe_event(EventTopic.SONG_REQUEST_ADDED, self._emit(self.songRequestAdded)),
                subscribe_event(EventTopic.SONG_REQUEST_DELETED, self._emit(self.songRequestDeleted)),
            ]
        )

    def stop(self) -> None:
        while self._subs:
            self._subs.pop()()
        self._started = False

    def _emit(self, signal: QtCore.SignalInstance) -> Callable[[Any], None]:
        def handler(payload: Any) -> None:
            QtCore.QTimer.singleShot(0, lambda: signal.emit(payload))

        return handler


_hub: Optional[QtEventHub] = None


def get_event_hub() -> QtEventHub:
    global _hub
    if _hub is None:
        _hub = QtEventHub()
        _hub.start()
    return _hub
