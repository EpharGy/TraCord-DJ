"""Status indicator panel (v2)."""
from __future__ import annotations

from typing import Dict

from PySide6 import QtCore, QtWidgets


class StatusPanel(QtWidgets.QGroupBox):
    _ENTRIES = [
        ("discord", "Discord"),
        ("listener", "Traktor Listener"),
        ("spout", "Spout"),
        ("midi", "MIDI"),
    ]

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Status", parent)
        form = QtWidgets.QFormLayout(self)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)

        self._labels: Dict[str, QtWidgets.QLabel] = {}
        for key, title in self._ENTRIES:
            label = QtWidgets.QLabel("Unknown")
            form.addRow(f"{title}:", label)
            self._labels[key] = label

    def set_status(self, key: str, text: str, *, color: str | None = None) -> None:
        label = self._labels.get(key)
        if not label:
            return
        label.setText(text)
        label.setStyleSheet(f"color: {color};" if color else "")
