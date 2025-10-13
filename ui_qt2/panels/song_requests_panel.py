"""Song requests panel (v2) with Date/Time/User/Artist/Title columns."""
from __future__ import annotations

from typing import Iterable, Tuple

from PySide6 import QtCore, QtWidgets


class SongRequestsPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Song Requests", parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["#", "Date", "Time", "User", "Artist", "Title"])
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

        # Fixed panel width as requested
        self.setFixedWidth(600)

        # Elide long text with '...'
        self.table.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)

        # No row selection highlight
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Apply initial column layout
        self._apply_column_layout()

    def set_requests(self, rows: Iterable[Tuple[int, str, str, str, str, str]]) -> None:
        data = list(rows)
        self.table.setRowCount(len(data))
        for row_index, (request_number, date_str, time_str, user, artist, title) in enumerate(data):
            for col_index, value in enumerate((request_number, date_str, time_str, user, artist, title)):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.table.setItem(row_index, col_index, item)
        # Re-apply column layout to respect caps and eliding
        QtCore.QTimer.singleShot(0, self._apply_column_layout)

    def clear(self) -> None:
        self.table.setRowCount(0)

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_column_layout()

    def showEvent(self, event):  # type: ignore[override]
        super().showEvent(event)
        QtCore.QTimer.singleShot(0, self._apply_column_layout)

    def _apply_column_layout(self) -> None:
        """Apply fixed/dynamic column widths within a 600px panel and cap oversized columns.

        - Fixed widths: #, Date, Time
        - Interactive: User, Artist
        - Stretch: Title (consumes remaining space)
        - Text is elided to fit within each column
        """
        try:
            header = self.table.horizontalHeader()
            header.setMinimumSectionSize(24)
            # Fixed for first three columns; interactive for User, Artist; Title stretches
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Stretch)

            # Prefer actual viewport width when available to avoid tiny overflows
            viewport_w = self.table.viewport().width()
            if viewport_w and viewport_w > 0:
                available = viewport_w
            else:
                # Conservative fallback if viewport not yet sized
                available = 600 - 32

            # Fixed columns
            w_num = 36
            w_date = 96
            w_time = 72
            fixed_total = w_num + w_date + w_time

            remaining = max(100, available - fixed_total)

            # Distribute remaining: User 30%, Artist 70% (Title will stretch)
            w_user = int(remaining * 0.30)
            w_artist = remaining - w_user

            # Minimums and caps
            w_user = min(w_user, 60)
            w_artist = min(w_artist, 125)

            # Apply widths (initial values; user can expand interactive columns)
            header.resizeSection(0, w_num)
            header.resizeSection(1, w_date)
            header.resizeSection(2, w_time)
            header.resizeSection(3, w_user)
            header.resizeSection(4, w_artist)
        except Exception:
            pass
