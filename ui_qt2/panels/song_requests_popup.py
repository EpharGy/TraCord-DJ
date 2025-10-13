"""Always-on-top popup window to view and clear Song Requests (v2)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from PySide6 import QtCore, QtWidgets

from config.settings import Settings
from tracord.core.events import EventTopic, emit_event
from ui_qt2.signals import get_event_hub
from utils.logger import get_logger

logger = get_logger(__name__)


class SongRequestsPopup(QtWidgets.QDialog):
    """Small, always-on-top popup showing requests with a one-click clear action."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Song Requests")
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.resize(605, 360)

        layout = QtWidgets.QVBoxLayout(self)

        # Columns: [✓], #, Date, Time, User, Artist, Title
        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["", "#", "Date", "Time", "User", "Artist", "Title"])  # action on the left
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.table.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.table)

        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(24)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)       # tick
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)       # number
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)       # date
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)       # time
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Interactive) # user
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Interactive) # artist
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.Stretch)     # title

        # React to resize and initial show for proper widths
        self._apply_column_layout()

        # Subscribe to events so popup stays in sync
        hub = get_event_hub()
        hub.songRequestAdded.connect(lambda _payload: self.reload_song_requests())
        hub.songRequestDeleted.connect(lambda _payload: self.reload_song_requests())

        # Initial load
        self.reload_song_requests()

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_column_layout()

    def showEvent(self, event):  # type: ignore[override]
        super().showEvent(event)
        # Try to match main panel widths first, then ensure caps via fallback layout
        def _after_show():
            if not self._apply_column_layout_from_main():
                self._apply_column_layout()
        QtCore.QTimer.singleShot(0, _after_show)

    def _apply_column_layout_from_main(self) -> bool:
        """Copy current widths from the main Song Requests panel, if available.

        Mapping: popup [tick, #, Date, Time, User, Artist, Title]
                 main  [     #, Date, Time, User, Artist, Title]
        """
        try:
            window = self.parent()
            if window is None:
                return False
            srp = getattr(window, "song_requests_panel", None)
            if srp is None:
                return False
            main_table = getattr(srp, "table", None)
            if main_table is None:
                return False
            mh = main_table.horizontalHeader()
            ph = self.table.horizontalHeader()

            # Read widths from main panel
            w_num = mh.sectionSize(0)
            w_date = mh.sectionSize(1)
            w_time = mh.sectionSize(2)
            w_user = mh.sectionSize(3)
            w_artist = mh.sectionSize(4)

            # Tick stays fixed at 24 to align visuals
            w_tick = 24

            # Apply to popup (Title stretches automatically)
            ph.resizeSection(0, w_tick)
            ph.resizeSection(1, w_num)
            ph.resizeSection(2, w_date)
            ph.resizeSection(3, w_time)
            ph.resizeSection(4, w_user)
            ph.resizeSection(5, w_artist)
            return True
        except Exception:
            return False

    def _apply_column_layout(self) -> None:
        """Mirror main panel spacing: tick/#/date/time fixed, user/artist interactive, title stretches."""
        h = self.table.horizontalHeader()
        # Fixed columns (match main panel logic; tick added as fixed)
        w_tick = 24
        w_num = 24
        w_date = 75
        w_time = 75

        # Prefer actual viewport width; fall back to dialog width minus some padding
        viewport_w = self.table.viewport().width()
        available = viewport_w if viewport_w and viewport_w > 0 else max(300, self.width() - 32)

        fixed_total = w_tick + w_num + w_date + w_time
        remaining = max(100, available - fixed_total)

        # Distribute remaining: User 30%, Artist 70% (Title stretches)
        w_user = int(remaining * 0.30)
        w_artist = remaining - w_user

        # Caps similar to main panel
        w_user = min(w_user, 75)
        w_artist = min(w_artist, 120)

        # Apply widths
        h.resizeSection(0, w_tick)
        h.resizeSection(1, w_num)
        h.resizeSection(2, w_date)
        h.resizeSection(3, w_time)
        h.resizeSection(4, w_user)
        h.resizeSection(5, w_artist)
        # Title stretches (section 6)

    def reload_song_requests(self) -> None:
        try:
            path = Path(Settings.SONG_REQUESTS_FILE)
            rows: list[Tuple[int, str, str, str, str, str]] = []
            if path.exists():
                items = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(items, list):
                    for idx, item in enumerate(items, start=1):
                        rn = item.get("RequestNumber")
                        try:
                            rn_int = int(rn) if rn is not None else idx
                        except Exception:
                            rn_int = idx
                        date_str = str(item.get("Date", ""))
                        time_str = str(item.get("Time", ""))
                        user = str(item.get("User", ""))
                        artist = str(item.get("Artist", ""))
                        title = str(item.get("Title", ""))
                        if not (artist and title):
                            song = str(item.get("Song", ""))
                            if " - " in song:
                                artist, title = [p.strip() for p in song.split(" - ", 1)]
                            else:
                                artist, title = "", song
                        rows.append((rn_int, date_str, time_str, user, artist, title))
                    rows.sort(key=lambda r: r[0])
            self._set_rows(rows)
        except Exception as e:
            logger.warning(f"Failed to load song requests in popup: {e}")
            self._set_rows([])

    def _set_rows(self, rows: list[Tuple[int, str, str, str, str, str]]) -> None:
        self.table.setRowCount(len(rows))
        for row_index, (rn, date, time_, user, artist, title) in enumerate(rows):
            # Data cells (shifted by one because col 0 is the action)
            for col_index, value in enumerate((rn, date, time_, user, artist, title), start=1):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.table.setItem(row_index, col_index, item)

            # Action button at far-left
            actions = QtWidgets.QWidget(self.table)
            hbox = QtWidgets.QHBoxLayout(actions)
            hbox.setContentsMargins(4, 0, 4, 0)
            hbox.setSpacing(6)

            clear_btn = QtWidgets.QToolButton(actions)
            clear_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton))
            clear_btn.setToolTip("Clear request")
            clear_btn.setAutoRaise(True)
            clear_btn.clicked.connect(lambda _, num=rn: self._delete_request(num))

            hbox.addWidget(clear_btn)
            hbox.addStretch(1)
            self.table.setCellWidget(row_index, 0, actions)

    def _delete_request(self, request_number: int) -> None:
        try:
            path = Path(Settings.SONG_REQUESTS_FILE)
            items = []
            if path.exists():
                try:
                    items = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    items = []
            # Capture info for logging before removal
            removed_info = None
            for it in items:
                try:
                    if int(it.get("RequestNumber", 0) or 0) == request_number:
                        removed_info = {
                            "RequestNumber": request_number,
                            "User": it.get("User", ""),
                            "Artist": it.get("Artist", ""),
                            "Title": it.get("Title", "") or it.get("Song", ""),
                        }
                        break
                except Exception:
                    pass
            # Remove by RequestNumber
            items = [it for it in items if int(it.get("RequestNumber", 0) or 0) != request_number]
            # Renumber
            for idx, it in enumerate(items, start=1):
                it["RequestNumber"] = idx
            path.write_text(json.dumps(items, indent=2), encoding="utf-8")
            if removed_info:
                logger.info(
                    "Song request cleared via popup: #%s | %s | %s - %s",
                    removed_info.get("RequestNumber"),
                    removed_info.get("User"),
                    removed_info.get("Artist"),
                    removed_info.get("Title"),
                )
            emit_event(EventTopic.SONG_REQUEST_DELETED, {"RequestNumber": request_number})
        except Exception as e:
            logger.error(f"Failed to delete request #{request_number}: {e}")
        finally:
            self.reload_song_requests()