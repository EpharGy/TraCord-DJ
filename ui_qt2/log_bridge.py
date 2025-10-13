"""Stdlib logging handler to forward logs to Qt UI (v2)."""
from __future__ import annotations

import logging

from PySide6 import QtCore

from ui_qt2.signals import get_event_hub


class QtLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._hub = get_event_hub()

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        level = record.levelname.lower()
        QtCore.QTimer.singleShot(0, lambda: self._hub.logMessage.emit(message, level))


_handler: QtLogHandler | None = None


def install_qt_log_handler(level: int = logging.INFO) -> QtLogHandler:
    global _handler
    if _handler is None:
        _handler = QtLogHandler()
        _handler.setLevel(level)
        logging.getLogger().addHandler(_handler)
    return _handler
