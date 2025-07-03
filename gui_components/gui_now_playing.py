import tkinter as tk
from tkinter import ttk
from utils.events import subscribe, emit
import random
from config.settings import Settings
from utils.traktor import load_collection_json
from utils.harmonic_keys import open_key_int_to_str
import os
from PIL import ImageTk
from utils.logger import debug, info, warning, error
import threading
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from mutagen._file import File as MutagenFile
from PIL import Image, ImageTk
import io
from utils.spout_sender_helper import SpoutGLHelper, SPOUTGL_AVAILABLE

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
        self.button_row.columnconfigure(2, weight=1)
        self.button_row.columnconfigure(3, weight=0)

        # Traktor Listener Toggle Button (left)
        self.traktor_listener_btn = ttk.Button(self.button_row, text="⭕ Enable Traktor Listener", width=25, style="TButton")
        self.traktor_listener_btn.grid(row=0, column=0, padx=(0, 4))

        # Spout Cover Art Toggle Button (center)
        self.spout_toggle_btn = ttk.Button(self.button_row, text="⭕ Enable Spout", width=25, style="TButton")
        self.spout_toggle_btn.grid(row=0, column=1, padx=(0, 4))

        # Spacer (expandable)
        spacer = tk.Frame(self.button_row)
        spacer.grid(row=0, column=2, sticky="ew")

        # Random Song Button (far right)
        self.random_button = ttk.Button(self.button_row, text="🎲", width=3, command=self.play_random_song)
        self.random_button.grid(row=0, column=3, sticky="e", padx=(0, 2))

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
        subscribe("song_played", self.update_now_playing)
        self._coverart_img = None  # Keep reference to avoid garbage collection
        # Spout
        self.spout_sender = None
        self.spout_enabled = False
        self._last_spout_image = None

    def set_traktor_listener_command(self, cmd):
        self.traktor_listener_btn.config(command=cmd)

    def set_spout_toggle_command(self, cmd):
        self.spout_toggle_btn.config(command=cmd)

    def set_traktor_listener_state(self, on: bool):
        if on:
            self.traktor_listener_btn.config(text="⭕ Disable Traktor Listener", style="Red.TButton")
        else:
            self.traktor_listener_btn.config(text="⭕ Enable Traktor Listener", style="TButton")

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

    def play_random_song(self):
        songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
        if not songs:
            self.update_now_playing(None)
            return
        song = random.choice(songs)
        from utils.song_matcher import get_song_info
        # Use get_song_info to standardize the song dict
        song_info = get_song_info(song.get('artist', ''), song.get('title', ''), songs)
        emit("song_played", song_info)

    def _start_spout_sender(self):
        if not SPOUTGL_AVAILABLE:
            warning("SpoutGL is not installed. Cannot start Spout sender.")
            return
        if self.spout_sender is None:
            self.spout_sender = SpoutGLHelper(sender_name="TraCordDJ CoverArt", width=1080, height=1080)
            self.spout_sender.start()
            info("[SpoutGL] Sender started.")
            # Send blank image on startup
            self._send_blank_spout_image()
        # If we have a last cover image, send it
        if self._last_spout_image is not None:
            self._send_spout_image(self._last_spout_image)

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
                from PIL import Image
                img = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
                self.spout_sender.send_pil_image(img)
                info(f"[SpoutGL] Sent blank/transparent image via SpoutGL: {1080}x{1080}")
            except Exception as e:
                warning(f"[SpoutGL] Error sending blank image: {e}")

    def update_now_playing(self, song_info):
        debug(f"[NowPlayingPanel] update_now_playing called with song_info: {song_info}")
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
        display = f"{artist}\n{title}" #Confirm before changing
        if album:
            display += f"\n[{album}]" 
        if bpm or key_str:
            display += f"\n{bpm}BPM | {key_str}" #Confirm before changing
        self.label.config(text=display)
        # Update cover art from audio file in a background thread
        audio_file_path = song_info.get('audio_file_path')
        if audio_file_path and os.path.exists(audio_file_path):
            def load_cover_art():
                try:
                    img_data = None
                    ext = os.path.splitext(audio_file_path)[1].lower()
                    info(f"[CoverArt] Attempting extraction for file type: {ext}")
                    if ext == '.flac':
                        audio = FLAC(audio_file_path)
                        if audio.pictures:
                            img_data = audio.pictures[0].data
                    elif ext in ('.mp3', '.m4a', '.aac', '.ogg'):
                        audio = MutagenFile(audio_file_path)
                        if audio is not None and hasattr(audio, 'tags') and audio.tags:
                            # For MP3 with ID3 tags
                            if isinstance(audio, MP3) and isinstance(audio.tags, ID3):
                                for tag in audio.tags.values():
                                    if isinstance(tag, APIC):
                                        img_data = getattr(tag, 'data', None)
                                        break
                            else:
                                # For other formats, try to find a tag with 'data'
                                for tag in audio.tags.values():
                                    if hasattr(tag, 'data'):
                                        img_data = tag.data
                                        break
                                    elif isinstance(tag, bytes):
                                        img_data = tag
                                        break
                    else:
                        # Fallback for other formats
                        audio = MutagenFile(audio_file_path)
                        if audio is not None and hasattr(audio, 'pictures') and audio.pictures:
                            img_data = audio.pictures[0].data
                    if img_data:
                        img_original = Image.open(io.BytesIO(img_data))
                        info(f"[CoverArt] Extracted image file type: {img_original.format}")
                        # For Spout: always resize to 1080x1080 and copy
                        img_for_spout = img_original.resize((1080, 1080), resample=3).copy()
                        # For GUI: resize to COVER_SIZE and copy
                        img_resized = img_original.resize((COVER_SIZE, COVER_SIZE), resample=3).copy()
                        cover_img = ImageTk.PhotoImage(img_resized)
                        def update_gui():
                            self._coverart_img = cover_img
                            self.coverart_label.config(image=self._coverart_img, bg="#111")
                            # Spout: send 1080x1080 image if enabled
                            self._last_spout_image = img_for_spout
                            if self.spout_enabled and self.spout_sender is not None:
                                self._send_spout_image(img_for_spout)
                        self.coverart_label.after(0, update_gui)
                        return
                    else:
                        warning(f"[CoverArt] Song had no cover art to extract: {audio_file_path}")
                        # Spout: send blank if enabled
                        if self.spout_enabled and self.spout_sender is not None:
                            self._send_blank_spout_image()
                except Exception as e:
                    warning(f"[CoverArt] Error extracting cover art: {e}")
                    try:
                        with open('data/Debug_unmatched_songs.txt', 'a', encoding='utf-8') as debug_file:
                            debug_file.write(f"Error extracting cover art for {audio_file_path}: {e}\n")
                    except Exception as log_error:
                        error(f"[CoverArt] Failed to log error to Debug_unmatched_songs.txt: {log_error}")
                    # Spout: send blank if enabled
                    if self.spout_enabled and self.spout_sender is not None:
                        self._send_blank_spout_image()
                def clear_gui():
                    self.coverart_label.config(image='', bg="#222")
                self.coverart_label.after(0, clear_gui)
            threading.Thread(target=load_cover_art, daemon=True).start()
        else:
            self.coverart_label.config(image='', bg="#222")
            # Spout: send blank if enabled
            if self.spout_enabled and self.spout_sender is not None:
                self._send_blank_spout_image()
