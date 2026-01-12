"""Song requests panel (v2) with Date/Time/User/Artist/Title columns."""
from __future__ import annotations

from typing import Iterable, Tuple

from PySide6 import QtCore, QtWidgets


class SongRequestsPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Song Requests", parent)
        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["", "#", "Date", "Time", "User", "BPM", "Artist", "Title"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        button_row = QtWidgets.QHBoxLayout()
        self.clear_button = QtWidgets.QPushButton("Clear All")
        self.popup_button = QtWidgets.QPushButton("Open Popup")
        self.popup_button.setEnabled(True)
        self.harmonic_button = QtWidgets.QPushButton("Harmonic Mix")
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        button_row.addWidget(self.harmonic_button)
        button_row.addWidget(self.popup_button)
        layout.addLayout(button_row)

        # Minimum panel width; allow expanding on window resize
        self.setMinimumWidth(600)

        # Elide long text with '...'
        self.table.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)

        # No row selection highlight
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Apply initial column layout
        self._apply_column_layout()

        self._on_set_harmonic = None

    def set_harmonic_handler(self, handler) -> None:
        self._on_set_harmonic = handler

    def set_requests(self, rows: Iterable[Tuple[int, str, str, str, str, str, str]]) -> None:
        data = list(rows)
        self.table.setRowCount(len(data))
        for row_index, (request_number, date_str, time_str, user, bpm, artist, title) in enumerate(data):
            actions = QtWidgets.QWidget(self.table)
            hbox = QtWidgets.QHBoxLayout(actions)
            hbox.setContentsMargins(2, 0, 2, 0)
            hbox.setSpacing(4)

            a_btn = QtWidgets.QToolButton(actions)
            a_btn.setText("A")
            a_btn.setToolTip("Set as Song A")
            a_btn.setAutoRaise(True)
            a_btn.clicked.connect(lambda _, r=request_number, d=date_str, t=time_str, u=user, b=bpm, ar=artist, ti=title: self._emit_harmonic("A", r, d, t, u, b, ar, ti))

            b_btn = QtWidgets.QToolButton(actions)
            b_btn.setText("B")
            b_btn.setToolTip("Set as Song B")
            b_btn.setAutoRaise(True)
            b_btn.clicked.connect(lambda _, r=request_number, d=date_str, t=time_str, u=user, b=bpm, ar=artist, ti=title: self._emit_harmonic("B", r, d, t, u, b, ar, ti))

            hbox.addWidget(a_btn)
            hbox.addWidget(b_btn)
            hbox.addStretch(1)
            self.table.setCellWidget(row_index, 0, actions)

            for col_index, value in enumerate((request_number, date_str, time_str, user, bpm, artist, title), start=1):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.table.setItem(row_index, col_index, item)
        # Re-apply column layout to respect caps and eliding
        QtCore.QTimer.singleShot(0, self._apply_column_layout)

    def _emit_harmonic(self, role: str, req_no, date_str, time_str, user, bpm, artist, title) -> None:
        if callable(self._on_set_harmonic):
            payload = {
                "RequestNumber": req_no,
                "Date": date_str,
                "Time": time_str,
                "User": user,
                "Bpm": bpm,
                "Artist": artist,
                "Title": title,
            }
            try:
                self._on_set_harmonic(role, payload)
            except Exception:
                pass

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

        # Fixed widths: Actions, #, Date, Time, BPM
        # Interactive: User, Artist
        # Stretch: Title (consumes remaining space)
        - Text is elided to fit within each column
        """
        try:
            header = self.table.horizontalHeader()
            header.setMinimumSectionSize(24)
            # Fixed: Actions, #, Date, Time, BPM; interactive: User, Artist; stretch: Title
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeMode.Stretch)

            # Prefer actual viewport width when available to avoid tiny overflows
            viewport_w = self.table.viewport().width()
            if viewport_w and viewport_w > 0:
                available = viewport_w
            else:
                # Conservative fallback if viewport not yet sized
                available = 600 - 32

            # Fixed columns
            w_actions = 42
            w_num = 24
            w_date = 75
            w_time = 45
            w_bpm = 55
            fixed_total = w_actions + w_num + w_date + w_time + w_bpm

            remaining = max(100, available - fixed_total)

            # Distribute remaining: User 30%, Artist 70% (Title will stretch)
            w_user = int(remaining * 0.30)
            w_artist = remaining - w_user

            # Minimums and caps
            w_user = min(w_user, 75)
            w_artist = min(w_artist, 120)

            # Apply widths (initial values; user can expand interactive columns)
            header.resizeSection(0, w_actions)
            header.resizeSection(1, w_num)
            header.resizeSection(2, w_date)
            header.resizeSection(3, w_time)
            header.resizeSection(4, w_user)
            header.resizeSection(5, w_bpm)
            header.resizeSection(6, w_artist)
        except Exception:
            pass
