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
        # Attach GUI handler to the ROOT logger so we capture both tracord and 3rd-party logs once
        # and allow tracord logs to also flow to RichHandler on root for pretty console output.
        try:
            # If previously attached to BASE_LOGGER in older versions, remove it
            try:
                BASE_LOGGER.removeHandler(_gui_handler)  # type: ignore[arg-type]
            except Exception:
                pass
            BASE_LOGGER.propagate = True
        except Exception:
            pass
    root_logger = logging.getLogger()
    if _gui_handler not in root_logger.handlers:
        root_logger.addHandler(_gui_handler)
    # Remove plain stream handlers to avoid writing to closed stdout/stderr when the GUI captures logs,
    # but keep RichHandler if present so console output stays pretty.
    for handler in list(root_logger.handlers):
        if handler is _gui_handler:
            continue
        try:
            from rich.logging import RichHandler  # type: ignore

            is_rich = isinstance(handler, RichHandler)
        except Exception:
            is_rich = False
        if isinstance(handler, logging.StreamHandler) and not is_rich:
            root_logger.removeHandler(handler)
    _gui_handler.callback = callback


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
