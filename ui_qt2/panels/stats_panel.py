"""Stats panel (v2)."""
from __future__ import annotations

from typing import Dict

from PySide6 import QtCore, QtWidgets


class StatsPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Stats", parent)
        grid = QtWidgets.QGridLayout(self)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(6)

        self._values: Dict[str, QtWidgets.QLabel] = {}

        row = 0
        # Session heading
        session_lbl = QtWidgets.QLabel("Session")
        session_lbl.setStyleSheet("font-weight: 600; margin-top: 2px;")
        grid.addWidget(session_lbl, row, 0, 1, 2)
        row += 1
        for key, title in (
            ("session_song_searches", "Searches"),
            ("session_song_requests", "Requests"),
            ("session_song_plays", "Plays"),
        ):
            grid.addWidget(QtWidgets.QLabel(title + ":"), row, 0)
            value = QtWidgets.QLabel("0")
            value.setObjectName(f"stat_{key}")
            grid.addWidget(value, row, 1)
            self._values[key] = value
            row += 1

        # Spacer between sections
        grid.setRowMinimumHeight(row, 4)
        row += 1

        # Total heading
        total_lbl = QtWidgets.QLabel("Total")
        total_lbl.setStyleSheet("font-weight: 600; margin-top: 6px;")
        grid.addWidget(total_lbl, row, 0, 1, 2)
        row += 1
        for key, title in (
            ("total_song_searches", "Searches"),
            ("total_song_requests", "Requests"),
            ("total_song_plays", "Plays"),
        ):
            grid.addWidget(QtWidgets.QLabel(title + ":"), row, 0)
            value = QtWidgets.QLabel("0")
            value.setObjectName(f"stat_{key}")
            grid.addWidget(value, row, 1)
            self._values[key] = value
            row += 1

        grid.setColumnStretch(1, 1)

    def update_stats(self, stats: Dict[str, int]) -> None:
        for key, label in self._values.items():
            label.setText(str(stats.get(key, 0)))
