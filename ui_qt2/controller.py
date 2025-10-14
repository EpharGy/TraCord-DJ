"""Qt controller (v2) – UI wiring for panels, stats, requests, and collection refresh."""
from __future__ import annotations

import base64
import random
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
from utils.stats import load_stats, reset_global_stats, reset_session_stats, increment_song_play
from utils.traktor import refresh_collection_json, load_collection_json
from utils.song_matcher import get_song_info
from tracord.utils.coverart import ensure_variants
from utils.midi_helper import MidiHelper
from utils.spout_sender_helper import SpoutGLHelper, SPOUTGL_AVAILABLE, SPOUT_SIZE
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
        self._spout = None  # type: SpoutGLHelper | None
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
        # Kick off a collection refresh shortly after startup (reuse same code as the Refresh button)
        # Delay to let the UI settle and avoid initial freeze during heavy file IO
        try:
            QtCore.QTimer.singleShot(1200, self._refresh_collection)
        except Exception:
            pass

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

        # Send cover art via Spout if enabled; if no cover, push a transparent frame to clear previous image
        try:
            if self._spout:
                from PIL import Image as _PILImage
                pil_img = None
                if pm is not None:
                    from PySide6 import QtGui
                    img = pm.toImage()
                    if not img.isNull():
                        from PIL.ImageQt import fromqimage as pil_fromqimage
                        pil_img = pil_fromqimage(img).convert("RGBA")
                if pil_img is None:
                    pil_img = _PILImage.new("RGBA", (SPOUT_SIZE, SPOUT_SIZE), (0, 0, 0, 0))
                self._spout.send_pil_image(pil_img)
        except Exception:
            # Avoid UI disruption if spout conversion fails
            pass

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
            cp.bind("settings", self._open_settings)
        except Exception:
            pass

        # Song Requests panel actions
        try:
            srp = self.window.song_requests_panel
            srp.clear_button.clicked.connect(self._clear_requests)
            srp.popup_button.clicked.connect(self._open_requests_popup)
        except Exception:
            pass

    def _open_settings(self) -> None:
        try:
            from ui_qt2.settings_dialog import SettingsDialog

            dlg = SettingsDialog(self.window)
            dlg.exec()
        except Exception as e:
            logger.warning(f"Failed to open Settings dialog: {e}")

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
        # Lazily create helper and start/stop sender
        if enabled:
            if not SPOUTGL_AVAILABLE:
                logger.warning("SpoutGL is not available; please install SpoutGL/pyopengl/glfw")
                enabled = False
            else:
                if self._spout is None:
                    self._spout = SpoutGLHelper()
                try:
                    self._spout.start()
                    logger.info("Spout sender enabled")
                except Exception as e:
                    logger.error(f"Failed to start Spout sender: {e}")
                    enabled = False
        else:
            if self._spout is not None:
                try:
                    self._spout.stop()
                except Exception:
                    pass
                self._spout = None
            logger.info("Spout sender disabled")

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
            # Update status
            self.window.set_status("discord", "Connected", color="#8fda8f")
            # Populate Bot Info panel
            try:
                user = getattr(bot_obj, "user", None)
                bot_name = str(user) if user is not None else "Unknown"
                bot_id = str(getattr(user, "id", "")) if user is not None else ""
            except Exception:
                bot_name, bot_id = "Unknown", ""

            try:
                cmds = bot_obj.tree.get_commands() if hasattr(bot_obj, "tree") else []
                cmd_count = len(cmds) if isinstance(cmds, (list, tuple)) else 0
            except Exception:
                cmd_count = 0

            try:
                from version import __version__ as _ver
            except Exception:
                _ver = ""

            try:
                self.window.set_bot_info(name=bot_name, bot_id=str(bot_id), commands=cmd_count, version=_ver)
            except Exception:
                pass

            logger.info(f"Discord bot ready: {bot_name}")
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
        try:
            # 1) Load collection and pick a random song
            songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
            payload: dict
            if songs:
                song = random.choice(songs)
                info = get_song_info(song.get("artist", ""), song.get("title", ""), songs)
                artist = info.get("artist", "Unknown Artist")
                title = info.get("title", "Unknown Title")
                album = info.get("album", "")
                cover_b64 = ""
                try:
                    audio_path = info.get("audio_file_path") or ""
                    if isinstance(audio_path, str) and audio_path and os.path.exists(audio_path):
                        ui_sz = int(getattr(Settings, "COVER_SIZE", 200) or 200)
                        spout_sz = int(getattr(Settings, "SPOUT_COVER_SIZE", 1080) or 1080)
                        result = ensure_variants(
                            audio_path,
                            sizes={"ui": (ui_sz, ui_sz), "spout": (spout_sz, spout_sz)},
                            base64_variant="ui",
                        )
                        if result.base64_png:
                            cover_b64 = result.base64_png
                except Exception:
                    cover_b64 = ""
                payload = {"artist": artist, "title": title, "album": album, "coverart_base64": cover_b64}
            else:
                # Fallback to a bundled demo image if collection is missing
                cover_path = os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots", "overlay_coverart_1.png")
                cover_b64 = ""
                try:
                    cover_abs = os.path.abspath(cover_path)
                    if os.path.exists(cover_abs):
                        with open(cover_abs, "rb") as f:
                            cover_b64 = base64.b64encode(f.read()).decode("ascii")
                except Exception:
                    cover_b64 = ""
                payload = {"artist": "Demo Artist", "title": "Demo Track", "album": "Demo Album", "coverart_base64": cover_b64}

            # 2) Increment stats and emit event to drive the full workflow
            try:
                increment_song_play()
            except Exception:
                pass
            emit_event(EventTopic.SONG_PLAYED, payload)
        except Exception as e:
            logger.warning(f"Debug inject failed: {e}")

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
