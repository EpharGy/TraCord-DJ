"""Qt signal bridge for the domain event bus (v2)."""
from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6 import QtCore

from tracord.core.events import EventTopic, subscribe_event
from utils.logger import get_logger

logger = get_logger(__name__)


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
        # Core subscriptions
        self._subs.extend(
            [
                subscribe_event(EventTopic.SONG_PLAYED, self._on_song_event),
                subscribe_event(EventTopic.STATS_UPDATED, self._emit(self.statsUpdated)),
                subscribe_event(EventTopic.SONG_REQUEST_ADDED, self._emit(self.songRequestAdded)),
                subscribe_event(EventTopic.SONG_REQUEST_DELETED, self._emit(self.songRequestDeleted)),
            ]
        )
    # If needed, we can also listen to TRAKTOR_SONG for diagnostics only.
    # Avoid forwarding it to songPlayed to prevent duplicate handling when
    # services emit both SONG_PLAYED and TRAKTOR_SONG.
    # self._subs.append(subscribe_event(EventTopic.TRAKTOR_SONG, self._on_traktor_song))

    def stop(self) -> None:
        while self._subs:
            self._subs.pop()()
        self._started = False

    def _emit(self, signal: QtCore.SignalInstance) -> Callable[[Any], None]:
        def handler(payload: Any) -> None:
            # Emit directly; Qt will queue to the receiver's thread if needed
            try:
                signal.emit(payload)
            except Exception:
                # Fallback to queued invoke if any runtime issue occurs
                QtCore.QTimer.singleShot(0, lambda: signal.emit(payload))

        return handler

    # --- Internal handlers to aid diagnostics and unify SONG events ---
    def _on_song_event(self, payload: Any) -> None:
        try:
            logger.debug("[GUI Hub] Received SONG_PLAYED")
        except Exception:
            pass
        # Emit directly; queued to main thread automatically if needed
        self.songPlayed.emit(payload)

    # def _on_traktor_song(self, payload: Any) -> None:
    #     try:
    #         logger.debug("[GUI Hub] Received TRAKTOR_SONG")
    #     except Exception:
    #         pass
    #     # Do not forward to songPlayed to avoid duplicate controller handling
    #     # self.songPlayed.emit(payload)


_hub: Optional[QtEventHub] = None


def get_event_hub() -> QtEventHub:
    global _hub
    if _hub is None:
        _hub = QtEventHub()
        _hub.start()
    return _hub
