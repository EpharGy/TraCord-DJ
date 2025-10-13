"""Bot information summary panel (v2)."""
from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class BotInfoPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Bot Info", parent)
        layout = QtWidgets.QFormLayout(self)
        layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)

        self._name = QtWidgets.QLabel("–")
        self._id = QtWidgets.QLabel("–")
        self._commands = QtWidgets.QLabel("0")

        layout.addRow("Name:", self._name)
        layout.addRow("App ID:", self._id)
        layout.addRow("Commands:", self._commands)

    def set_info(self, *, name: str, id: str, commands: str, version: str | None = None) -> None:
        self._name.setText(name)
        self._id.setText(id)
        self._commands.setText(commands)
        # Version is shown in window title now; ignore here
