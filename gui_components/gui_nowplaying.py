import tkinter as tk
from tkinter import ttk

class NowPlayingPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Now Playing (Coming Soon)", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.placeholder = ttk.Label(self, text="Now Playing info will appear here.", anchor="center")
        self.placeholder.grid(row=0, column=0, sticky="nsew")
