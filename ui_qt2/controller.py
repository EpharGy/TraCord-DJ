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
from services.web_overlay import WebOverlayServer
from utils.stats import load_stats, reset_global_stats, reset_session_stats
from utils.traktor import refresh_collection_json
from utils.midi_helper import MidiHelper
from services.traktor_listener import TraktorBroadcastListener
from services.discord_bot import DiscordBotController
from main import DJBot

logger = get_logger(__name__)


class QtController(QtCore.QObject):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        window.set_controller(self)

        self._connect_ui()
        self._connect_controls()

        # Backends
        self._midi = None  # type: MidiHelper | None
        self._listener = None  # type: TraktorBroadcastListener | None
        self._listener_timer = QtCore.QTimer(self)
        self._listener_timer.setInterval(1000)
        self._listener_timer.timeout.connect(self._poll_listener_status)
        self._listener_status_last: str | None = None
        self._discord: DiscordBotController | None = None
        self._overlay_server: WebOverlayServer | None = None

        # Populate UI on startup
        self.push_stats_update()
        self.reload_song_requests()
        # Autostart services after a short delay so UI settles first
        QtCore.QTimer.singleShot(1500, self._auto_start_services)

    # --- Slots called by MainWindow/hub ---
    def handle_song_event(self, payload: dict) -> None:
        # Text
        artist = str(payload.get("artist", ""))
        title = str(payload.get("title", ""))
        album = str(payload.get("album", ""))
        if artist or title:
            logger.info(f"[Traktor] Song Played: {artist} - {title} [{album}]")
        # GUI: Artist, Title, [Album], Extra
        bpm = str(payload.get("bpm", "")).strip()
        key = str(payload.get("key", "")).strip()
        extra = (f"{bpm}BPM | {key}".strip(" |")) if (bpm or key) else ""
        if any([artist, title, album, extra]):
            self.window.now_playing_panel.set_track_fields(artist, title, album, extra)
        else:
            self.window.now_playing_panel.set_track_info("No track info available")
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

        # Fire MIDI on song change if enabled
        try:
            if self._midi and self._midi.enabled:
                self._midi.send_song_change()
        except Exception:
            # Any MIDI errors are handled in helper; keep UI responsive
            pass

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
                        try:
                            rn = item.get("RequestNumber", idx)
                            rn_int = int(rn)
                        except Exception:
                            rn_int = idx
                        date_str = str(item.get("Date", ""))
                        time_str = str(item.get("Time", ""))
                        user = str(item.get("User", ""))
                        # Prefer structured fields when present, fallback to legacy combined 'Song'
                        artist = str(item.get("Artist", "")).strip()
                        title = str(item.get("Title", "")).strip()
                        if not (artist or title):
                            song = str(item.get("Song", ""))
                            if " | " in song:
                                artist, title = song.split(" | ", 1)
                            else:
                                artist, title = "", song
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
        np.overlayRequested.connect(self._open_overlay)

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
                cp.bind("bot", self._on_toggle_discord)
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
        # Lazily create and start/stop Traktor broadcast listener
        if enabled:
            if self._listener is None:
                port = getattr(Settings, "TRAKTOR_BROADCAST_PORT", 8000)
                self._listener = TraktorBroadcastListener(port, status_callback=self._on_listener_status)
            self._listener.start()
            self._listener_timer.start()
            logger.info("[Traktor] Listener enabling…")
        else:
            if self._listener is not None:
                self._listener.stop()
            self._listener_timer.stop()
            logger.info("[Traktor] Listener disabled")
        # Reflect state immediately (waiting while trying to connect)
        self.window.now_playing_panel.set_listener_state(enabled)
        if enabled:
            self.window.set_status("listener", "Waiting", color="#f0ad4e")
        else:
            self.window.set_status("listener", "Off", color="#ff4d4f")

    def _on_listener_status(self, status: str) -> None:
        # Called from listener thread; schedule on UI thread
        QtCore.QTimer.singleShot(0, lambda: self._update_listener_status(status))

    def _update_listener_status(self, status: str) -> None:
        text = {
            "waiting": "Waiting",
            "connected": "Connected",
            "off": "Off",
        }.get(status, status.capitalize())
        color = {
            "Connected": "#8fda8f",
            "Waiting": "#f0ad4e",
            "Off": "#ff4d4f",
        }.get(text, "#bbbbbb")
        self.window.set_status("listener", text, color=color)
        # Log only on changes to avoid spam
        if text != self._listener_status_last:
            if text == "Connected":
                logger.info("[Traktor] Connected, receiving stream…")
            elif text == "Waiting":
                logger.info("[Traktor] Waiting for Traktor broadcast…")
            self._listener_status_last = text

    def _poll_listener_status(self) -> None:
        # Poll transient statuses from listener queue
        try:
            if self._listener is not None:
                self._listener.poll_status()
        except Exception:
            pass

    def _on_toggle_spout(self, enabled: bool) -> None:
        self.window.now_playing_panel.set_spout_state(enabled)
        self.window.set_status("spout", "Connected" if enabled else "Off", color="#8fda8f" if enabled else "#ff4d4f")

    def _on_toggle_midi(self, enabled: bool) -> None:
        # Lazily create helper
        if enabled:
            if self._midi is None:
                # Use configured device name from settings.json (MIDI_DEVICE)
                self._midi = MidiHelper(getattr(Settings, "MIDI_DEVICE", None))
            ok = self._midi.enable()
            enabled = enabled and ok
        else:
            if self._midi is not None:
                self._midi.disable()
        # Reflect final state in UI
        self.window.now_playing_panel.set_midi_state(enabled)
        self.window.set_status("midi", "Connected" if enabled else "Off", color="#8fda8f" if enabled else "#ff4d4f")
        # Log errors if any
        if self._midi and self._midi.get_error():
            logger.warning(f"MIDI: {self._midi.get_error()}")

    # --- Commands ---
    def _clear_requests(self) -> None:
        try:
            data_path = Path(Settings.SONG_REQUESTS_FILE)
            data_path.parent.mkdir(parents=True, exist_ok=True)
            # Count existing items for logging
            count_before = 0
            try:
                if data_path.exists():
                    cur_items = json.loads(data_path.read_text(encoding="utf-8"))
                    if isinstance(cur_items, list):
                        count_before = len(cur_items)
            except Exception:
                count_before = 0

            from utils.helpers import safe_write_json
            safe_write_json(str(data_path), [])
            logger.info("All song requests (%s) cleared from main panel", count_before)
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

    def _open_overlay(self) -> None:
        try:
            # Lazily construct server instance
            if self._overlay_server is None:
                self._overlay_server = WebOverlayServer(
                    host=getattr(Settings, "OVERLAY_HOST", "127.0.0.1"),
                    port=getattr(Settings, "OVERLAY_PORT", 5000),
                )
            # Start if not running
            if not self._overlay_server.is_running:
                self._overlay_server.start_server()

            # Open in default browser
            import webbrowser

            url = f"http://{self._overlay_server.host}:{self._overlay_server.port}/"
            webbrowser.open(url, new=2)
            logger.info(f"Overlay opened in browser: {url}")
        except Exception as e:
            logger.error(f"Failed to open overlay: {e}")

    # --- Autostart helpers ---
    def _auto_start_services(self) -> None:
        try:
            # Start overlay server in background (do not open browser)
            if self._overlay_server is None:
                self._overlay_server = WebOverlayServer(
                    host=getattr(Settings, "OVERLAY_HOST", "127.0.0.1"),
                    port=getattr(Settings, "OVERLAY_PORT", 5000),
                )
            if not self._overlay_server.is_running:
                self._overlay_server.start_server()
        except Exception as e:
            logger.warning(f"Overlay autostart failed: {e}")

        # Start Discord bot if token present
        try:
            token = getattr(Settings, "DISCORD_TOKEN", None) or Settings.get("DISCORD_TOKEN")
            if token:
                self._ensure_discord_controller()
                if self._discord and not self._discord.is_running:
                    self._discord.start_discord_bot()
            else:
                logger.debug("Discord token not set; skipping autostart")
        except Exception as e:
            logger.warning(f"Discord autostart failed: {e}")
        # Reflect initial bot state in controls
        QtCore.QTimer.singleShot(200, self._refresh_bot_button)

    def _ensure_discord_controller(self) -> None:
        if self._discord is None:
            callbacks = {
                "on_status": lambda text, color=None: self.window.set_status("discord", text, color=color),
                "on_ready": self._on_discord_ready,
                "on_error": self._on_discord_error,
                "on_stopped": self._on_discord_stopped,
            }
            # Settings acts like a dict via .get
            self._discord = DiscordBotController(DJBot, Settings, gui_callbacks=callbacks)
        # Always refresh label after ensuring controller
        self._refresh_bot_button()

    # --- Discord controls ---
    def _on_start_discord(self) -> None:
        try:
            self._ensure_discord_controller()
            if self._discord and not self._discord.is_running:
                self._discord.start_discord_bot()
            else:
                logger.debug("Discord bot already running")
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
        finally:
            self._refresh_bot_button()

    def _on_stop_discord(self) -> None:
        try:
            if self._discord and self._discord.is_running:
                self._discord.stop_discord_bot()
            else:
                logger.debug("Discord bot not running")
        except Exception as e:
            logger.error(f"Failed to stop Discord bot: {e}")
        finally:
            self._refresh_bot_button()

    def _on_toggle_discord(self) -> None:
        if self._discord and self._discord.is_running:
            self._on_stop_discord()
        else:
            self._on_start_discord()

    def _refresh_bot_button(self) -> None:
        try:
            running = bool(self._discord and self._discord.is_running)
            self.window.controls_panel.set_button_text("bot", "⏹ Stop Bot" if running else "▶ Start Bot")
            self.window.controls_panel.set_enabled("bot", True)
        except Exception:
            pass

    # --- Discord callbacks ---
    def _on_discord_ready(self, bot_obj) -> None:
        try:
            name = getattr(bot_obj, "user", None)
            self.window.set_status("discord", "Connected", color="#8fda8f")
            logger.info(f"Discord bot ready: {name}")
            self._refresh_bot_button()
        except Exception:
            pass

    def _on_discord_error(self, message: str) -> None:
        try:
            logger.error(f"Discord error: {message}")
            self.window.set_status("discord", "Off", color="#ff4d4f")
            self._refresh_bot_button()
        except Exception:
            pass

    def _on_discord_stopped(self) -> None:
        try:
            self.window.set_status("discord", "Off", color="#ff4d4f")
            self._refresh_bot_button()
        except Exception:
            pass

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
