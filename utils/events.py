"""Legacy event helpers delegating to the new tracord.infra.events bus."""
from typing import Any, Callable

from tracord.infra.events import emit as _emit
from tracord.infra.events import get_event_bus, subscribe as _subscribe
from tracord.infra.events import unsubscribe as _unsubscribe


def subscribe(event_name: str, callback: Callable[..., None]) -> None:
    _subscribe(event_name, callback)


def unsubscribe(event_name: str, callback: Callable[..., None]) -> None:
    _unsubscribe(event_name, callback)


def emit(event_name: str, data: Any = None) -> None:
    _emit(event_name, data)


# Expose bus for advanced callers (maintaining backward compat).
event_system = get_event_bus()
