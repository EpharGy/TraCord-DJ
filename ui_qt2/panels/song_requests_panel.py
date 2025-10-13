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

        # Fixed panel width as requested
        self.setFixedWidth(600)

        # Elide long text with '...'
        self.table.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)

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
        - Dynamic with caps: User, Artist, Title
        - Text is elided to fit within each column
        """
        try:
            header = self.table.horizontalHeader()
            # Use fixed resize mode so widths we set are respected
            for i in range(self.table.columnCount()):
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Fixed)

            # Base metrics
            fixed_panel_width = 600
            # Estimate available width for the table viewport inside the group box
            lay = self.layout()
            margins = lay.contentsMargins() if lay is not None else QtCore.QMargins(8, 8, 8, 8)
            frame = self.table.frameWidth() * 2
            vscroll = self.table.verticalScrollBar().sizeHint().width() if self.table.verticalScrollBar().isVisible() else 0
            padding = margins.left() + margins.right() + frame + vscroll
            available = max(300, fixed_panel_width - padding)

            # Fixed columns
            w_num = 36
            w_date = 96
            w_time = 72
            fixed_total = w_num + w_date + w_time

            remaining = max(100, available - fixed_total)

            # Distribute remaining: User 20%, Artist 35%, Title 45%
            w_user = int(remaining * 0.20)
            w_artist = int(remaining * 0.35)
            w_title = remaining - w_user - w_artist

            # Minimums
            w_user = max(w_user, 80)
            w_artist = max(w_artist, 120)
            w_title = max(w_title, 140)

            # Maximum caps
            w_user = min(w_user, 120)
            w_artist = min(w_artist, 200)
            w_title = min(w_title, 240)

            # Apply widths
            header.resizeSection(0, w_num)
            header.resizeSection(1, w_date)
            header.resizeSection(2, w_time)
            header.resizeSection(3, w_user)
            header.resizeSection(4, w_artist)
            header.resizeSection(5, w_title)
        except Exception:
            pass
