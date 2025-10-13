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
    tracord_logger = logging.getLogger("tracord")
    # Ensure the handler is only added once
    if _handler not in tracord_logger.handlers:
        tracord_logger.addHandler(_handler)
    # Ensure the tracord logger actually emits at the desired level
    if tracord_logger.level == logging.NOTSET or tracord_logger.level > level:
        tracord_logger.setLevel(level)
    # Propagate so terminal still shows logs via root handler
    tracord_logger.propagate = True
    return _handler
