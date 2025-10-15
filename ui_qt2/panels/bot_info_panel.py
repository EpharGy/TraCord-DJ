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
        self._last_refresh = QtWidgets.QLabel("–")
        self._new_songs = QtWidgets.QLabel("0")

        layout.addRow("Name:", self._name)
        layout.addRow("App ID:", self._id)
        layout.addRow("Commands:", self._commands)
        layout.addRow("Last Refresh:", self._last_refresh)
        layout.addRow("New Songs:", self._new_songs)

    def set_info(
        self,
        *,
        name: str,
        id: str,
        commands: str,
        version: str | None = None,
        last_refresh: str | None = None,
        new_songs: int | str | None = None,
    ) -> None:
        self._name.setText(name)
        # Mask App ID: show '**' followed by the last 4 characters
        try:
            s = str(id) if id is not None else ""
            masked = f"**{s[-4:]}" if s else ""
        except Exception:
            masked = ""
        self._id.setText(masked)
        self._commands.setText(commands)
        if last_refresh is not None:
            self._last_refresh.setText(str(last_refresh))
        if new_songs is not None:
            try:
                self._new_songs.setText(str(int(new_songs)))
            except Exception:
                self._new_songs.setText(str(new_songs))
        # Version is shown in window title now; ignore here

    def set_collection_info(self, *, last_refresh: str, new_songs: int | str) -> None:
        self._last_refresh.setText(str(last_refresh))
        try:
            self._new_songs.setText(str(int(new_songs)))
        except Exception:
            self._new_songs.setText(str(new_songs))
