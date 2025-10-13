"""Qt controller (v2) – handles UI updates and provides a tiny debug injector."""
from __future__ import annotations

import base64
import os
from PySide6 import QtCore

from ui_qt2.main_window import MainWindow
from ui_qt2.panels.now_playing_panel import NowPlayingPanel
from tracord.core.events import EventTopic, emit_event


class QtController(QtCore.QObject):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        window.set_controller(self)
        self._connect_ui()

    # Stubs to satisfy MainWindow calls
    def handle_song_event(self, payload: dict) -> None:
        # Extract text info
        artist = str(payload.get("artist", ""))
        title = str(payload.get("title", ""))
        album = str(payload.get("album", ""))
        lines = [v for v in (title, artist, album) if v]
        self.window.now_playing_panel.set_track_info("\n".join(lines) or "No track info available")

        # Decode cover art if present
        cover_b64 = payload.get("coverart_base64")
        pixmap = None
        if isinstance(cover_b64, str) and cover_b64:
            try:
                from PySide6 import QtGui  # local import to avoid top-level import if unused

                data = base64.b64decode(cover_b64)
                pm = QtGui.QPixmap()
                if pm.loadFromData(data):
                    pixmap = pm
            except Exception:
                pixmap = None
        self.window.now_playing_panel.set_cover_pixmap(pixmap)

    def push_stats_update(self) -> None:
        pass

    def reload_song_requests(self) -> None:
        pass

    # --- Debug helpers ---
    def debug_inject_song(self) -> None:
        """Emit a demo SONG_PLAYED event to validate UI wiring (Ctrl+T)."""
        cover_path = os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots", "overlay_coverart_1.png")
        cover_b64 = ""
        try:
            cover_abs = os.path.abspath(cover_path)
            if os.path.exists(cover_abs):
                with open(cover_abs, "rb") as f:
                    cover_b64 = base64.b64encode(f.read()).decode("ascii")
        except Exception:
            cover_b64 = ""

        emit_event(
            EventTopic.SONG_PLAYED,
            {
                "artist": "Demo Artist",
                "title": "Demo Track",
                "album": "Demo Album",
                "coverart_base64": cover_b64,
            },
        )

    # --- Internal wiring ---
    def _connect_ui(self) -> None:
        np: NowPlayingPanel = self.window.now_playing_panel
        np.toggledListener.connect(self._on_toggle_listener)
        np.toggledSpout.connect(self._on_toggle_spout)
        np.toggledMidi.connect(self._on_toggle_midi)

    # --- Toggle handlers (UI-only) ---
    def _on_toggle_listener(self, enabled: bool) -> None:
        self.window.now_playing_panel.set_listener_state(enabled)
        self.window.set_status("listener", "Listening" if enabled else "Disabled", color="#8fda8f" if enabled else "#bbbbbb")

    def _on_toggle_spout(self, enabled: bool) -> None:
        self.window.now_playing_panel.set_spout_state(enabled)
        self.window.set_status("spout", "Enabled" if enabled else "Disabled", color="#8fda8f" if enabled else "#bbbbbb")

    def _on_toggle_midi(self, enabled: bool) -> None:
        self.window.now_playing_panel.set_midi_state(enabled)
        self.window.set_status("midi", "Enabled" if enabled else "Disabled", color="#8fda8f" if enabled else "#bbbbbb")
