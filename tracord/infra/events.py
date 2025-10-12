"""Thread-safe pub/sub event bus for TraCord DJ."""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any, Callable, DefaultDict, Iterable, List, Protocol

from utils.logger import get_logger


logger = get_logger(__name__)


class Subscriber(Protocol):
    def __call__(self, payload: Any) -> None:
        ...


class EventBus:
    """A lightweight, thread-safe event dispatcher."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Subscriber]] = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(self, event: str, callback: Subscriber) -> None:
        with self._lock:
            if callback not in self._subscribers[event]:
                self._subscribers[event].append(callback)
                logger.debug(f"[EventBus] Subscribed to '{event}': {callback}")

    def unsubscribe(self, event: str, callback: Subscriber) -> None:
        with self._lock:
            callbacks = self._subscribers.get(event)
            if not callbacks:
                return
            try:
                callbacks.remove(callback)
                logger.debug(f"[EventBus] Unsubscribed from '{event}': {callback}")
            except ValueError:
                pass
            if not callbacks:
                self._subscribers.pop(event, None)

    def emit(self, event: str, payload: Any = None) -> None:
        with self._lock:
            callbacks = list(self._subscribers.get(event, ()))
        if not callbacks:
            return
        for callback in callbacks:
            try:
                callback(payload)
            except Exception as exc:  # pragma: no cover - keep bus alive
                logger.warning(f"[EventBus] Subscriber error for '{event}': {exc}")

    def listeners(self, event: str) -> Iterable[Subscriber]:
        with self._lock:
            return tuple(self._subscribers.get(event, ()))


# Global bus used by legacy convenience helpers
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    return _event_bus


def subscribe(event: str, callback: Subscriber) -> None:
    _event_bus.subscribe(event, callback)


def unsubscribe(event: str, callback: Subscriber) -> None:
    _event_bus.unsubscribe(event, callback)


def emit(event: str, payload: Any = None) -> None:
    _event_bus.emit(event, payload)
