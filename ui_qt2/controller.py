"""Qt controller (v2) – UI wiring for panels, stats, requests, and collection refresh."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Tuple

from PySide6 import QtCore

from config.settings import Settings
from tracord.core.events import EventTopic, emit_event
from ui_qt2.main_window import MainWindow
from ui_qt2.panels.now_playing_panel import NowPlayingPanel
from ui_qt2.panels.song_requests_popup import SongRequestsPopup
from utils.logger import get_logger
from utils.stats import load_stats, reset_global_stats, reset_session_stats
from utils.traktor import refresh_collection_json

logger = get_logger(__name__)


class QtController(QtCore.QObject):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        window.set_controller(self)

        self._connect_ui()
        self._connect_controls()

        # Populate UI on startup
        self.push_stats_update()
        self.reload_song_requests()

    # --- Slots called by MainWindow/hub ---
    def handle_song_event(self, payload: dict) -> None:
        # Text
        artist = str(payload.get("artist", ""))
        title = str(payload.get("title", ""))
        album = str(payload.get("album", ""))
        lines = [v for v in (title, artist, album) if v]
        self.window.now_playing_panel.set_track_info("\n".join(lines) or "No track info available")
        # Cover art
        cover_b64 = payload.get("coverart_base64")
        pm = None
        if isinstance(cover_b64, str) and cover_b64:
            try:
                from PySide6 import QtGui

                data = base64.b64decode(cover_b64)
                pixmap = QtGui.QPixmap()
                if pixmap.loadFromData(data):
                    pm = pixmap
            except Exception:
                pm = None
        self.window.now_playing_panel.set_cover_pixmap(pm)

    def push_stats_update(self) -> None:
        try:
            stats = load_stats()
        except Exception:
            stats = {}
        defaults = {
            "session_song_searches": 0,
            "total_song_searches": 0,
            "session_song_plays": 0,
            "total_song_plays": 0,
            "session_song_requests": 0,
            "total_song_requests": 0,
        }
        for k, v in defaults.items():
            stats.setdefault(k, v)
        self.window.stats_panel.update_stats(stats)  # type: ignore[arg-type]

    def reload_song_requests(self) -> None:
        try:
            data_path = Path(Settings.SONG_REQUESTS_FILE)
            rows: list[Tuple[int, str, str, str, str, str]] = []
            if data_path.exists():
                items = json.loads(data_path.read_text(encoding="utf-8"))
                if isinstance(items, list):
                    for idx, item in enumerate(items, start=1):
                        rn = item.get("RequestNumber")
                        try:
                            rn_int = int(rn) if rn is not None else idx
                        except Exception:
                            rn_int = idx
                        user = str(item.get("User", ""))
                        # Support either combined Song or separate Artist/Title
                        artist = str(item.get("Artist", ""))
                        title = str(item.get("Title", ""))
                        if not (artist and title):
                            song = str(item.get("Song", ""))
                            if " - " in song:
                                artist, title = [p.strip() for p in song.split(" - ", 1)]
                            else:
                                artist, title = "", song
                        date_str = str(item.get("Date", ""))
                        time_str = str(item.get("Time", ""))
                        rows.append((rn_int, date_str, time_str, user, artist, title))
                    rows.sort(key=lambda r: r[0])
            self.window.set_requests(rows)
        except Exception as e:
            logger.warning(f"Failed to load song requests: {e}")
            self.window.set_requests([])

    # --- UI wiring ---
    def _connect_ui(self) -> None:
        np: NowPlayingPanel = self.window.now_playing_panel
        np.toggledListener.connect(self._on_toggle_listener)
        np.toggledSpout.connect(self._on_toggle_spout)
        np.toggledMidi.connect(self._on_toggle_midi)

    def _connect_controls(self) -> None:
        cp = self.window.controls_panel

        def _reset_session() -> None:
            reset_session_stats()
            self.push_stats_update()

        def _reset_global() -> None:
            reset_global_stats()
            self.push_stats_update()

        try:
            cp.bind("reset_session", _reset_session)
            cp.bind("reset_global", _reset_global)
            cp.bind("refresh", self._refresh_collection)
        except Exception:
            pass

        # Song Requests panel actions
        try:
            srp = self.window.song_requests_panel
            srp.clear_button.clicked.connect(self._clear_requests)
            srp.popup_button.clicked.connect(self._open_requests_popup)
        except Exception:
            pass

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

    # --- Commands ---
    def _clear_requests(self) -> None:
        try:
            data_path = Path(Settings.SONG_REQUESTS_FILE)
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.write_text("[]", encoding="utf-8")
            logger.info("Song Requests cleared")
        except Exception as e:
            logger.error(f"Failed to clear song requests: {e}")
        self.reload_song_requests()

    def _refresh_collection(self) -> None:
        try:
            traktor_path = Settings.TRAKTOR_PATH
            collection_json = Settings.COLLECTION_JSON_FILE
            excluded = Settings.EXCLUDED_ITEMS
            debug = Settings.DEBUG
            if not traktor_path or not os.path.exists(traktor_path):
                logger.warning("Traktor path not configured. Check settings.json.")
                return
            count = refresh_collection_json(traktor_path, collection_json, excluded, debug)
            logger.info(f"Collection refreshed: {count} songs processed")
        except Exception as e:
            logger.error(f"Collection refresh failed: {e}")

    # --- Debug ---
    def debug_inject_song(self) -> None:
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

    def _open_requests_popup(self) -> None:
        # Keep a reference on the controller; handle deleted C++ object safely
        popup = getattr(self, "_requests_popup", None)
        is_deleted = False
        try:
            # sip.isdeleted works with PySide6 as well
            import sip  # type: ignore

            if popup is not None:
                is_deleted = bool(sip.isdeleted(popup))
        except Exception:
            # Fallback: accessing property on a deleted object raises RuntimeError
            if popup is not None:
                try:
                    _ = popup.isVisible()  # may raise if deleted
                except RuntimeError:
                    is_deleted = True

        if popup is None or is_deleted or not popup.isVisible():
            self._requests_popup = SongRequestsPopup(self.window)
            self._requests_popup.show()
        else:
            self._requests_popup.raise_()
            self._requests_popup.activateWindow()
