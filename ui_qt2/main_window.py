"""Main window for the TraCord DJ Qt interface (v2)."""
from __future__ import annotations

from typing import Iterable, Tuple, TYPE_CHECKING

from PySide6 import QtCore, QtWidgets, QtGui

from ui_qt2.panels.bot_info_panel import BotInfoPanel
from ui_qt2.panels.controls_panel import ControlsPanel
from ui_qt2.panels.log_panel import LogPanel
from ui_qt2.panels.now_playing_panel import NowPlayingPanel
from ui_qt2.panels.song_requests_panel import SongRequestsPanel
from ui_qt2.panels.stats_panel import StatsPanel
from ui_qt2.panels.status_panel import StatusPanel
from ui_qt2.signals import get_event_hub
from version import __version__

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ui_qt2.controller import QtController


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"TraCord DJ - {__version__}")
        self.resize(1250, 700)
        self.controller: QtController | None = None

        hub = get_event_hub()
        hub.songPlayed.connect(self.on_song_played)
        hub.statsUpdated.connect(self.on_stats_updated)
        hub.songRequestAdded.connect(self.on_song_request_update)
        hub.songRequestDeleted.connect(self.on_song_request_update)
        hub.logMessage.connect(self.on_log_message)
        self._setup_layout()
        self._setup_shortcuts()
        # Initialize default statuses
        self.set_status("discord", "Off", color="#ff4d4f")
        self.set_status("listener", "Off", color="#ff4d4f")
        self.set_status("spout", "Off", color="#ff4d4f")
        self.set_status("midi", "Off", color="#ff4d4f")

    def _setup_layout(self) -> None:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left column
        left_column = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_column)
        left_layout.setSpacing(12)

        self.controls_panel = ControlsPanel()
        self.status_panel = StatusPanel()
        self.bot_info_panel = BotInfoPanel()
        self.stats_panel = StatsPanel()

        # Order: Controls -> Status -> Bot Info -> Stats
        left_layout.addWidget(self.controls_panel)
        left_layout.addWidget(self.status_panel)
        left_layout.addWidget(self.bot_info_panel)
        left_layout.addWidget(self.stats_panel)
        left_layout.addStretch(1)

        # Center column
        center_column = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center_column)
        center_layout.setSpacing(12)

        self.now_playing_panel = NowPlayingPanel()
        self.log_panel = LogPanel()

        center_layout.addWidget(self.now_playing_panel)
        center_layout.addWidget(self.log_panel)
        center_layout.setStretchFactor(self.now_playing_panel, 0)
        center_layout.setStretchFactor(self.log_panel, 1)

        # Right column
        right_column = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_column)
        right_layout.setSpacing(12)

        self.song_requests_panel = SongRequestsPanel()
        right_layout.addWidget(self.song_requests_panel)
        # Match Now Playing panel height
        self.song_requests_panel.setMinimumHeight(self.now_playing_panel.sizeHint().height())
        right_layout.addStretch(1)

        splitter.addWidget(left_column)
        splitter.addWidget(center_column)
        splitter.addWidget(right_column)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

    # --- Event Hub Slots ---
    def on_song_played(self, payload: dict) -> None:
        if self.controller:
            self.controller.handle_song_event(payload)

    def on_stats_updated(self, payload: object) -> None:  # noqa: D401 - Qt signature
        if self.controller:
            self.controller.push_stats_update()

    def on_song_request_update(self, payload: object) -> None:  # noqa: D401 - Qt signature
        if self.controller:
            self.controller.reload_song_requests()

    def on_log_message(self, message: str, level: str) -> None:
        self.log_panel.append_log(message, level)

    # --- Facade helpers ---
    def set_bot_info(self, *, name: str, bot_id: str, commands: int, version: str) -> None:
        self.bot_info_panel.set_info(name=name, id=bot_id, commands=str(commands), version=version)

    def set_status(self, key: str, text: str, *, color: str | None = None) -> None:
        self.status_panel.set_status(key, text, color=color)

    def set_requests(self, rows: Iterable[Tuple[int, str, str, str, str, str]]) -> None:
        self.song_requests_panel.set_requests(rows)

    def set_controller(self, controller: QtController) -> None:
        self.controller = controller

    def _setup_shortcuts(self) -> None:
        # Ctrl+T: inject demo song for quick UI validation
        sc = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+T"), self)
        sc.activated.connect(lambda: self.controller and self.controller.debug_inject_song())
