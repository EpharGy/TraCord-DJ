import tkinter as tk
from tkinter import ttk
from utils.events import subscribe

class NowPlayingPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Now Playing", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.label = ttk.Label(self, text="Now Playing info will appear here.", anchor="center", justify="left", font=("Arial", 16, "bold"))
        self.label.grid(row=0, column=0, sticky="nsew")
        subscribe("song_played", self.update_now_playing)

    def update_now_playing(self, song_info):
        if not song_info:
            self.label.config(text="No song info available.")
            return
        artist = song_info.get('artist', '')
        title = song_info.get('title', '')
        album = song_info.get('album', '')
        display = f"Artist: {artist}\nTitle: {title}"
        if album:
            display += f"\n[{album}]"
        self.label.config(text=display)
