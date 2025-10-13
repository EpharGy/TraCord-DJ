"""Log panel (v2)."""
from __future__ import annotations

from PySide6 import QtWidgets


class LogPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Log", parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

    def append_log(self, message: str, level: str) -> None:
        self.text_edit.appendPlainText(f"[{level.upper()}] {message}")
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
