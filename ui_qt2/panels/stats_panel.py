"""Stats panel (v2)."""
from __future__ import annotations

from typing import Dict

from PySide6 import QtCore, QtWidgets


class StatsPanel(QtWidgets.QGroupBox):
    _FIELDS = [
        ("session_song_searches", "Session Searches"),
        ("total_song_searches", "Total Searches"),
        ("session_song_plays", "Session Plays"),
        ("total_song_plays", "Total Plays"),
        ("session_song_requests", "Session Requests"),
        ("total_song_requests", "Total Requests"),
    ]

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Stats", parent)
        grid = QtWidgets.QGridLayout(self)
        grid.setHorizontalSpacing(15)
        self._values: Dict[str, QtWidgets.QLabel] = {}
        for row, (key, title) in enumerate(self._FIELDS):
            grid.addWidget(QtWidgets.QLabel(title + ":"), row, 0)
            value = QtWidgets.QLabel("0")
            value.setObjectName(f"stat_{key}")
            grid.addWidget(value, row, 1)
            self._values[key] = value
        grid.setColumnStretch(2, 1)

    def update_stats(self, stats: Dict[str, int]) -> None:
        for key, label in self._values.items():
            label.setText(str(stats.get(key, 0)))
