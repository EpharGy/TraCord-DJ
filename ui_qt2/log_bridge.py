"""Stdlib logging handler to forward logs to Qt UI (v2).

This installs a handler on the 'tracord' logger so any logs from the app's
modules (e.g., services.traktor_listener) are forwarded to the Qt event hub.
"""
from __future__ import annotations

import logging

from PySide6 import QtCore

from ui_qt2.signals import get_event_hub


class QtLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._hub = get_event_hub()

    def emit(self, record: logging.LogRecord) -> None:
        # Minimal formatting: include logger name prefix
        message = f"{record.name}: {self.format(record)}"
        level = record.levelname.lower()
        # Emit directly; Qt signals are thread-safe and will be queued to the UI thread
        try:
            self._hub.logMessage.emit(message, level)
        except Exception:
            # As a fallback, schedule on the UI thread
            QtCore.QTimer.singleShot(0, lambda: self._hub.logMessage.emit(message, level))


_handler: QtLogHandler | None = None


def install_qt_log_handler(level: int = logging.INFO) -> QtLogHandler:
    """Install GUI log handler on the 'tracord' logger tree.

    Attaching to the tracord hierarchy ensures internal app logs appear in the GUI
    without duplicating third-party/root logs. Avoid double-attachment.
    """
    global _handler
    if _handler is None:
        _handler = QtLogHandler()
        _handler.setLevel(level)
    # Attach to our logger tree
    tracord_logger = logging.getLogger("tracord")
    if _handler not in tracord_logger.handlers:
        tracord_logger.addHandler(_handler)
    if tracord_logger.level == logging.NOTSET or tracord_logger.level > level:
        tracord_logger.setLevel(level)
    tracord_logger.propagate = True

    # Also capture discord.* logs so important bot lifecycle messages appear in GUI
    discord_logger = logging.getLogger("discord")
    if _handler not in discord_logger.handlers:
        discord_logger.addHandler(_handler)
    if discord_logger.level == logging.NOTSET or discord_logger.level > level:
        discord_logger.setLevel(level)
    discord_logger.propagate = True
    return _handler
