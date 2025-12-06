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
from ui_qt2.signals import get_event_hub
from version import __version__
from utils.logger import get_logger

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ui_qt2.controller import QtController


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"TraCord DJ - {__version__}")
        self.resize(1250, 600)  # Initial window size
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
        self.bot_info_panel = BotInfoPanel()
        self.stats_panel = StatsPanel()

    # Order: Controls -> Bot Info -> Stats (Status panel removed; buttons reflect state)
        left_layout.addWidget(self.controls_panel)
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
        # Left stays compact by default and right column takes remaining space; user can drag handles
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

    # --- Event Hub Slots ---
    def on_song_played(self, payload: dict) -> None:
        try:
            get_logger(__name__).debug("[GUI] on_song_played slot fired")
        except Exception:
            pass
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
        # Reflect state on the relevant control button for quick glance
        state_txt = (text or "").lower()
        # Prefer explicit color if provided
        if (color or "").lower() in {"#8fda8f"}:
            state = "on"
        elif (color or "").lower() in {"#f0ad4e"}:
            state = "waiting"
        elif (color or "").lower() in {"#ff4d4f"}:
            state = "off"
        else:
            # Fallback by keywords used across the app and discord.py lifecycle
            waiting_keywords = ("wait", "start", "starting", "login", "logging", "sync", "initial", "connecting", "enable", "enabling")
            on_keywords = ("connected", "ready", "running")
            if any(k in state_txt for k in on_keywords):
                state = "on"
            elif any(k in state_txt for k in waiting_keywords):
                state = "waiting"
            else:
                state = "off"
        try:
            if key == "discord":
                self.controls_panel.set_state("bot", state)
            elif key == "listener":
                self.now_playing_panel.set_control_state("listener", state)
            elif key == "spout":
                self.now_playing_panel.set_control_state("spout", state)
            elif key == "midi":
                self.now_playing_panel.set_control_state("midi", state)
        except Exception:
            pass

    def set_requests(self, rows: Iterable[Tuple[int, str, str, str, str, str]]) -> None:
        self.song_requests_panel.set_requests(rows)

    def set_controller(self, controller: QtController) -> None:
        self.controller = controller

    def set_collection_info(self, *, last_refresh: str, new_songs: int | str) -> None:
        self.bot_info_panel.set_collection_info(last_refresh=last_refresh, new_songs=new_songs)

    def _setup_shortcuts(self) -> None:
        # Ctrl+T: inject demo song for quick UI validation
        sc = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+T"), self)
        sc.activated.connect(lambda: self.controller and self.controller.debug_inject_song())
