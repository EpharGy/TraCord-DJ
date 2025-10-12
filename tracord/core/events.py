"""Typed event definitions and helpers for TraCord DJ."""
from __future__ import annotations

from enum import StrEnum
from typing import Any, Callable, Dict, TypedDict

from tracord.infra.events import (
    emit as _emit,
    get_event_bus,
    subscribe as _subscribe,
    unsubscribe as _unsubscribe,
)


class SongEventPayload(TypedDict, total=False):
    artist: str
    title: str
    album: str
    bpm: float | int | str | None
    key: str
    genre: str
    audio_file_path: str
    coverart_base64: str
    timestamp: float


class SongRequestPayload(TypedDict, total=False):
    RequestNumber: int
    Date: str
    User: str
    Song: str


class EventTopic(StrEnum):
    SONG_PLAYED = "song_played"
    TRAKTOR_SONG = "traktor_song"
    SONG_REQUEST_ADDED = "song_request_added"
    SONG_REQUEST_DELETED = "song_request_deleted"
    STATS_UPDATED = "stats_updated"


EventHandler = Callable[[Any], None]


def subscribe_event(topic: EventTopic, handler: EventHandler) -> Callable[[], None]:
    """Register a handler for a typed event topic.

    Returns a callable that can be used to unsubscribe the handler.
    """

    def _adapter(payload: Any) -> None:
        handler(payload)

    _subscribe(topic.value, _adapter)

    def _unsubscribe_adapter() -> None:
        _unsubscribe(topic.value, _adapter)

    return _unsubscribe_adapter


def emit_event(topic: EventTopic, payload: SongEventPayload | SongRequestPayload | Dict[str, Any] | None = None) -> None:
    """Dispatch an event to all subscribers."""

    _emit(topic.value, payload)


__all__ = [
    "EventTopic",
    "SongEventPayload",
    "SongRequestPayload",
    "subscribe_event",
    "emit_event",
    "get_event_bus",
]
