"""Logging helpers and GUI bridge built on the stdlib logging module."""
from __future__ import annotations

import logging
from typing import Optional


BASE_LOGGER = logging.getLogger("tracord")
GUI_SUCCESS_MARKERS = ["✅", "🟢", "ready", "success", "complete"]
_gui_handler: Optional["GuiHandler"] = None


class GuiHandler(logging.Handler):
    """Forward log records to the GUI callback."""

    def __init__(self) -> None:
        super().__init__()
        self.callback = None
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - simple bridge
        if not self.callback:
            return
        try:
            message = self.format(record)
            gui_level = _map_record_to_gui_level(record, message)
            self.callback(message, gui_level)
        except Exception:  # noqa: BLE001 - guard against GUI errors
            self.handleError(record)


def _map_record_to_gui_level(record: logging.LogRecord, message: str) -> str:
    if record.levelno >= logging.ERROR:
        return "error"
    if record.levelno >= logging.WARNING:
        return "warning"
    if record.levelno == logging.INFO and any(marker in message for marker in GUI_SUCCESS_MARKERS):
        return "success"
    return "info"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger rooted under the ``tracord`` namespace."""

    if not name:
        return BASE_LOGGER
    if name.startswith("tracord"):
        return logging.getLogger(name)
    return logging.getLogger(f"tracord.{name}")


def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug logging for the tracord logger hierarchy."""

    BASE_LOGGER.setLevel(logging.DEBUG if enabled else logging.INFO)


def is_debug_enabled() -> bool:
    """Return True when the tracord logger is running at DEBUG level."""

    return BASE_LOGGER.level <= logging.DEBUG


def set_gui_callback(callback) -> None:
    """Register a GUI callback to receive log events."""

    global _gui_handler
    if _gui_handler is None:
        _gui_handler = GuiHandler()
        BASE_LOGGER.addHandler(_gui_handler)
    _gui_handler.callback = callback


def debug(message: str) -> None:
    BASE_LOGGER.debug(message)


def info(message: str) -> None:
    BASE_LOGGER.info(message)


def warning(message: str) -> None:
    BASE_LOGGER.warning(message)


def error(message: str) -> None:
    BASE_LOGGER.error(message)


class OutputCapture:
    """
    Captures output from stdout/stderr and routes it to both the original stream and a queue or callback (e.g., for GUI log panel).
    """
    def __init__(self, queue_obj, tag, original, gui_instance=None):
        self.queue = queue_obj
        self.tag = tag
        self.original = original
        self.gui = gui_instance

    def write(self, text):
        # Always write to original first (terminal)
        self.original.write(text)
        self.original.flush()
        # Then capture for GUI (only non-empty lines)
        if text.strip():
            self.queue.put((self.tag, text.strip()))

    def flush(self):
        self.original.flush()


# Backward compatibility re-exports kept above
