import tkinter as tk
from tkinter import ttk
from utils.events import subscribe, emit
import random
from config.settings import Settings
from utils.traktor import load_collection_json
from utils.harmonic_keys import open_key_int_to_str
import os

class NowPlayingPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Now Playing", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        # Temporary Random Song Button (easy to remove later)
        self.random_button = ttk.Button(self, text="🎲", width=3, command=self.play_random_song)
        self.random_button.grid(row=0, column=0, sticky="ne", padx=2, pady=(0, 6))
        # Dynamically set wraplength based on CONSOLE_PANEL_WIDTH from env
        panel_width = int(os.getenv('CONSOLE_PANEL_WIDTH', 500))
        wraplength = panel_width - 10
        self.label = tk.Label(self, text="Now Playing info will appear here.", anchor="w", justify="left", font=("Arial", 16, "bold"), wraplength=wraplength, padx=8, pady=4)
        self.label.grid(row=1, column=0, sticky="nsew")
        subscribe("song_played", self.update_now_playing)

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
