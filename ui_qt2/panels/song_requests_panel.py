"""Song requests panel (v2)."""
from __future__ import annotations

from typing import Iterable, Tuple

from PySide6 import QtCore, QtWidgets


class SongRequestsPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Song Requests", parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["#", "User", "Song"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        button_row = QtWidgets.QHBoxLayout()
        self.clear_button = QtWidgets.QPushButton("Clear All")
        self.popup_button = QtWidgets.QPushButton("Open Popup")
        self.popup_button.setEnabled(False)
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        button_row.addWidget(self.popup_button)
        layout.addLayout(button_row)

    def set_requests(self, rows: Iterable[Tuple[int, str, str]]) -> None:
        data = list(rows)
        self.table.setRowCount(len(data))
        for row_index, (request_number, user, song) in enumerate(data):
            for col_index, value in enumerate((request_number, user, song)):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.table.setItem(row_index, col_index, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def clear(self) -> None:
        self.table.setRowCount(0)
