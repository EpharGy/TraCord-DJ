import tkinter as tk
from tkinter import ttk
from utils.events import subscribe, emit
import random
from config.settings import Settings
from utils.traktor import load_collection_json
from utils.harmonic_keys import open_key_int_to_str
from utils.coverart import get_coverart_image
import os
from PIL import ImageTk

COVER_SIZE = 150  # px, square cover art dimension (move to .env later)

class NowPlayingPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Now Playing", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=0)  # Cover art column
        self.columnconfigure(1, weight=1)  # Info column
        self.rowconfigure(0, weight=0)  # Button row
        self.rowconfigure(1, weight=0)  # Content row (no vertical expansion)
        # Temporary Random Song Button (easy to remove later)
        self.random_button = ttk.Button(self, text="🎲", width=3, command=self.play_random_song)
        self.random_button.grid(row=0, column=1, sticky="ne", padx=2, pady=(0, 6))
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
        panel_width = int(os.getenv('CONSOLE_PANEL_WIDTH', 500))
        wraplength = panel_width - COVER_SIZE - 14
        self.label = tk.Label(self, text="Now Playing info will appear here.", anchor="w", justify="left", font=("Arial", 16, "bold"), wraplength=wraplength, padx=8, pady=4)
        self.label.grid(row=1, column=1, sticky="nw")
        subscribe("song_played", self.update_now_playing)
        self._coverart_img = None  # Keep reference to avoid garbage collection

    def play_random_song(self):
        songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
        if not songs:
            self.update_now_playing(None)
            return
        song = random.choice(songs)
        emit("song_played", song)

    def update_now_playing(self, song_info):
        if not song_info:
            self.label.config(text="No song info available.")
            self.coverart_label.config(image='', bg="#222")
            return
        artist = song_info.get('artist', '')
        title = song_info.get('title', '')
        album = song_info.get('album', '')
        bpm = song_info.get('bpm', '')
        key_int = song_info.get('musical_key', None)
        key_str = open_key_int_to_str(key_int) if key_int is not None else ''
        display = f"Artist: {artist}\nTitle: {title}"
        if album:
            display += f"\n[{album}]"
        if bpm or key_str:
            display += f"\nBPM: {bpm} | Key: {key_str}"
        self.label.config(text=display)
        # Update cover art
        coverart_id = song_info.get('cover_art_id') or song_info.get('cover_art') or song_info.get('coverart_id') or song_info.get('coverart')
        traktor_location = getattr(Settings, 'TRAKTOR_LOCATION', None)
        collection_filename = getattr(Settings, 'TRAKTOR_COLLECTION_FILENAME', None)
        version_folder = None
        if collection_filename:
            version_folder = os.path.basename(collection_filename).replace('collection.nml', '').strip('\\/')
        if coverart_id and version_folder and traktor_location:
            img = get_coverart_image(traktor_location, version_folder, coverart_id)
            if img:
                img = img.resize((COVER_SIZE, COVER_SIZE), resample=3)
                self._coverart_img = ImageTk.PhotoImage(img)
                self.coverart_label.config(image=self._coverart_img, bg="#111")
                return
        # No cover art found
        self.coverart_label.config(image='', bg="#222")
