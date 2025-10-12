import tkinter as tk
from tkinter import ttk
from utils.events import subscribe, emit
import random
from config.settings import Settings
from utils.traktor import load_collection_json
from utils.harmonic_keys import open_key_int_to_str
import os
from typing import Optional

from PIL import ImageTk
from utils.logger import debug, info, warning, error
import threading
from utils.spout_sender_helper import SpoutGLHelper, SPOUTGL_AVAILABLE
from utils.midi_helper import MidiHelper
from tracord.utils.coverart import CoverArtResult, blank_image, ensure_variants

info("[NowPlayingPanel] File loaded and logger is active.")

COVER_SIZE = Settings.COVER_SIZE if hasattr(Settings, 'COVER_SIZE') and Settings.COVER_SIZE else 150  # px, square cover art dimension

class NowPlayingPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        info("[NowPlayingPanel] __init__ called.")
        super().__init__(parent, text="Now Playing", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=0)  # Cover art column
        self.columnconfigure(1, weight=1)  # Info column
        self.rowconfigure(0, weight=0)  # Button row
        self.rowconfigure(1, weight=0)  # Content row (no vertical expansion)

        # --- New Button Row ---
        self.button_row = tk.Frame(self)
        self.button_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.button_row.columnconfigure(0, weight=0)
        self.button_row.columnconfigure(1, weight=0)
        self.button_row.columnconfigure(2, weight=0)
        self.button_row.columnconfigure(3, weight=0)
        self.button_row.columnconfigure(4, weight=1)
        self.button_row.columnconfigure(5, weight=0)

        # Traktor Listener Toggle Button (left)
        self.traktor_listener_btn = ttk.Button(self.button_row, text="⭕ Enable Listener", width=16, style="TButton")
        self.traktor_listener_btn.grid(row=0, column=0, padx=(0, 4))

        # Spout Cover Art Toggle Button (center left)
        self.spout_toggle_btn = ttk.Button(self.button_row, text="⭕ Enable Spout", width=15, style="TButton")
        self.spout_toggle_btn.grid(row=0, column=1, padx=(0, 4))

        # Open Overlay Button (center right)
        self.overlay_button = ttk.Button(self.button_row, text="🌐 Open Overlay", width=15, command=lambda: None)
        self.overlay_button.grid(row=0, column=2, padx=(0, 4))

        # MIDI Toggle Button (right of Overlay)
        self.midi_helper = MidiHelper(preferred_port_name=Settings.MIDI_DEVICE)
        self.midi_toggle_btn = ttk.Button(self.button_row, text="⭕ Enable MIDI", width=15, command=self.toggle_midi)
        self.midi_toggle_btn.grid(row=0, column=3, padx=(0, 4))

        # Spacer (expandable)
        spacer = tk.Frame(self.button_row)
        spacer.grid(row=0, column=4, sticky="ew")

        # Random Song Button (far right)
        self.random_button = ttk.Button(self.button_row, text="🎲", width=3, command=self.play_random_song)
        self.random_button.grid(row=0, column=5, sticky="e", padx=(0, 2))

        # --- End Button Row ---

        # Cover art frame (fixed size)
        self.coverart_frame = tk.Frame(self, width=COVER_SIZE, height=COVER_SIZE, bg="#222")
        self.coverart_frame.grid_propagate(False)
        self.coverart_frame.grid(row=1, column=0, sticky="nw", padx=(0, 0), pady=2)  # Set between padding to 0
        # Cover art label inside frame
        self.coverart_label = tk.Label(self.coverart_frame, bg="#222", relief="groove")
        self.coverart_label.place(x=0, y=0, width=COVER_SIZE, height=COVER_SIZE)
        # Info label (right)
        # Calculate wraplength for song data:
        # Formula: wraplength = CONSOLE_PANEL_WIDTH - border_left - border_right - left_padding - COVER_SIZE - between_padding - right_padding
        # (Assume border_left/right = 2px each, paddings = 5px each except between_padding=0)
        # wraplength = CONSOLE_PANEL_WIDTH - COVER_SIZE - 14
        panel_width = Settings.CONSOLE_PANEL_WIDTH if hasattr(Settings, 'CONSOLE_PANEL_WIDTH') and Settings.CONSOLE_PANEL_WIDTH else 500
        wraplength = panel_width - COVER_SIZE - 14
        self.label = tk.Label(self, text="Now Playing info will appear here.", anchor="w", justify="left", font=("Arial", 16, "bold"), wraplength=wraplength, padx=8, pady=4)
        self.label.grid(row=1, column=1, sticky="nw")
        subscribe("song_played", self._on_song_played_event)
        subscribe("traktor_song", self.handle_song_play)  # Subscribe to custom event from Traktor
        self._coverart_img = None  # Keep reference to avoid garbage collection
        # Spout
        self.spout_sender = None
        self.spout_enabled = False
        self._last_spout_image = None
        self._coverart_base64 = None  # Store last base64 coverart for event emission

    def set_traktor_listener_command(self, cmd):
        self.traktor_listener_btn.config(command=cmd)

    def set_spout_toggle_command(self, cmd):
        self.spout_toggle_btn.config(command=cmd)

    def set_overlay_command(self, cmd):
        self.overlay_button.config(command=cmd)

    def set_traktor_listener_state(self, on: bool):
        if on:
            self.traktor_listener_btn.config(text="⭕ Disable Listener", style="Red.TButton")
        else:
            self.traktor_listener_btn.config(text="⭕ Enable Listener", style="TButton")

    def set_spout_toggle_state(self, on: bool):
        self.spout_enabled = on
        if on:
            if not SPOUTGL_AVAILABLE:
                import tkinter.messagebox as mb
                mb.showwarning("Spout Not Installed", "SpoutGL is not installed. Please see the README for installation instructions to enable Spout cover art output.")
                self.spout_toggle_btn.config(text="⭕ Enable Spout", style="TButton")
                self.spout_enabled = False
                return
            self.spout_toggle_btn.config(text="⭕ Disable Spout", style="Red.TButton")
            self._start_spout_sender()
        else:
            self.spout_toggle_btn.config(text="⭕ Enable Spout", style="TButton")
            self._stop_spout_sender()

    # ------------------------------------------------------------------
    # Cover art processing helpers

    def _cover_art_sizes(self, include_spout: bool) -> dict[str, tuple[int, int]]:
        sizes = {"ui": (COVER_SIZE, COVER_SIZE)}
        if include_spout:
            spout_size = getattr(Settings, "SPOUT_COVER_SIZE", 1080) or 1080
            sizes["spout"] = (spout_size, spout_size)
        return sizes

    def _augment_song_info_with_cover_art(
        self,
        song_info: dict,
        *,
        include_spout: bool,
        on_complete,
    ) -> None:
        """Attach cover art assets to ``song_info`` asynchronously."""

        audio_file_path = song_info.get('audio_file_path')
        if not audio_file_path or not os.path.exists(audio_file_path):
            song_info['coverart_base64'] = ''
            on_complete(song_info, None)
            return

        def worker():
            try:
                result = ensure_variants(
                    audio_file_path,
                    sizes=self._cover_art_sizes(include_spout),
                    base64_variant="ui",
                )
                song_info['coverart_base64'] = result.base64_png or ''
                if not result.has_art:
                    warning(f"[CoverArt] No embedded artwork found: {audio_file_path}")
            except Exception as exc:  # pragma: no cover - guard threads
                warning(f"[CoverArt] Unexpected error processing artwork: {exc}")
                self._record_cover_art_failure(audio_file_path, f"Error extracting cover art: {exc}")
                result = None
                song_info['coverart_base64'] = ''
            on_complete(song_info, result)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_cover_art_to_gui(self, song_info: dict, result: Optional[CoverArtResult]) -> None:
        """Update GUI/spout output based on ``result``."""

        if result and result.has_art and 'ui' in result.variants:
            ui_image = result.variants['ui']
            cover_img = ImageTk.PhotoImage(ui_image)
            self._coverart_img = cover_img
            self.coverart_label.config(image=self._coverart_img, bg="#111")
            self._coverart_base64 = song_info.get('coverart_base64', '')

            if self.spout_enabled and self.spout_sender is not None:
                spout_image = result.variants.get('spout')
                if spout_image is None:
                    size = self._cover_art_sizes(include_spout=True)['spout']
                    spout_image = blank_image(size)
                self._last_spout_image = spout_image
                self._send_spout_image(spout_image)
        else:
            self._coverart_img = None
            self.coverart_label.config(image='', bg="#222")
            self._coverart_base64 = ''
            if self.spout_enabled and self.spout_sender is not None:
                self._send_blank_spout_image()

    def _record_cover_art_failure(self, audio_file_path: str, message: str) -> None:
        warning(f"[CoverArt] {message}: {audio_file_path}")
        try:
            with open('data/Debug_unmatched_songs.txt', 'a', encoding='utf-8') as debug_file:
                debug_file.write(f"{message}: {audio_file_path}\n")
        except Exception as log_error:  # pragma: no cover - diagnostics only
            error(f"[CoverArt] Failed to log cover art issue: {log_error}")

    def emit_song_with_coverart(self, song_info):
        """Extract cover art, add as base64, then emit song_played event."""

        def on_complete(info_with_art, _):
            emit("song_played", info_with_art)

        self._augment_song_info_with_cover_art(
            song_info,
            include_spout=False,
            on_complete=on_complete,
        )

    def handle_song_play(self, song_info):
        """Unified handler for any song play event (Traktor or random)."""
        def after_coverart_extracted(song_info_with_art):
            # Only emit the event, do not call update_now_playing directly
            self.label.after(0, lambda: emit("song_played", song_info_with_art))
        self.extract_coverart_and_continue(song_info, after_coverart_extracted)

    def extract_coverart_and_continue(self, song_info, callback):
        """Extract cover art, add as base64, then invoke callback."""

        def on_complete(info_with_art, _):
            callback(info_with_art)

        self._augment_song_info_with_cover_art(
            song_info,
            include_spout=False,
            on_complete=on_complete,
        )

    def play_random_song(self):
        songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
        if not songs:
            self.update_now_playing(None)
            return
        song = random.choice(songs)
        from utils.song_matcher import get_song_info
        # Use get_song_info to standardize the song dict
        song_info = get_song_info(song.get('artist', ''), song.get('title', ''), songs)
        self.handle_song_play(song_info)

    def _start_spout_sender(self):
        if not SPOUTGL_AVAILABLE:
            warning("SpoutGL is not installed. Cannot start Spout sender.")
            return
        if self.spout_sender is None:
            spout_size = getattr(Settings, "SPOUT_COVER_SIZE", 1080) or 1080
            self.spout_sender = SpoutGLHelper(sender_name="TraCordDJ CoverArt", width=spout_size, height=spout_size)
            self.spout_sender.start()
            info("[SpoutGL] Sender started.")
            # Send blank image on startup
            self._send_blank_spout_image()
        # If we have a last cover image, send it
        #if self._last_spout_image is not None:
        #    self._send_spout_image(self._last_spout_image)

    def _stop_spout_sender(self):
        if self.spout_sender is not None:
            try:
                self.spout_sender.stop()
                info("[SpoutGL] Sender stopped.")
            except Exception as e:
                warning(f"[SpoutGL] Error stopping sender: {e}")
            self.spout_sender = None

    def _send_spout_image(self, pil_img):
        if self.spout_sender is None:
            return
        try:
            self.spout_sender.send_pil_image(pil_img)
            info(f"[SpoutGL] Sent cover art via SpoutGL")
        except Exception as e:
            warning(f"[SpoutGL] Error sending image: {e}")

    def _send_blank_spout_image(self):
        if self.spout_sender is not None:
            try:
                spout_size = getattr(Settings, "SPOUT_COVER_SIZE", 1080) or 1080
                img = blank_image((spout_size, spout_size))
                self.spout_sender.send_pil_image(img)
                info(f"[SpoutGL] Sent blank/transparent image via SpoutGL: {spout_size}x{spout_size}")
            except Exception as e:
                warning(f"[SpoutGL] Error sending blank image: {e}")

    def toggle_midi(self):
        import tkinter.messagebox as mb
        if not self.midi_helper.enabled:
            if not self.midi_helper.enable():
                mb.showerror("MIDI Not Available", self.midi_helper.get_error() or "Unknown error.")
                self.midi_toggle_btn.config(text="⭕ MIDI Off", style="TButton")
                return
            self.midi_toggle_btn.config(text="⭕ MIDI On", style="Red.TButton")
            info("MIDI output enabled.")
        else:
            self.midi_helper.disable()
            self.midi_toggle_btn.config(text="⭕ MIDI Off", style="TButton")
            info("MIDI output disabled.")

    def _on_song_played_event(self, song_info):
        # Only update the GUI, do not emit or call handle_song_play here!
        self.update_now_playing(song_info)
        if self.midi_helper.enabled:
            self.midi_helper.send_song_change()

    # earmark: update_now_playing is now only needed for GUI updates, not for event emission
    # earmark: any direct emit("song_played", ...) outside emit_song_with_coverart/handle_song_play should be removed after confirming

    def update_now_playing(self, song_info):
        # Mask coverart_base64 in debug log
        log_info = dict(song_info) if song_info else {}
        if 'coverart_base64' in log_info:
            log_info['coverart_base64'] = f"<base64 string, {len(log_info['coverart_base64'])} bytes>"
        debug(f"[NowPlayingPanel] update_now_playing called with song_info: {log_info}")
        self._coverart_base64 = None
        if not song_info:
            self.label.config(text="No song info available.")
            self.coverart_label.config(image='', bg="#222")
            # Spout: send blank if enabled
            if self.spout_enabled and self.spout_sender is not None:
                self._send_blank_spout_image()
            return
        artist = song_info.get('artist', '')
        title = song_info.get('title', '')
        album = song_info.get('album', '')
        bpm = song_info.get('bpm', '')
        key_int = song_info.get('musical_key', None)
        key_str = open_key_int_to_str(key_int) if key_int is not None else ''
        display = f"{artist}\n{title}"
        if album:
            display += f"\n[{album}]" 
        if bpm or key_str:
            display += f"\n{bpm}BPM | {key_str}"
        self.label.config(text=display)
        include_spout = self.spout_enabled or self.spout_sender is not None

        def on_complete(info_with_art: dict, result: Optional[CoverArtResult]):
            self.coverart_label.after(0, lambda: self._apply_cover_art_to_gui(info_with_art, result))

        self._augment_song_info_with_cover_art(
            song_info,
            include_spout=include_spout,
            on_complete=on_complete,
        )
