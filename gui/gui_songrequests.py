import tkinter as tk
from tkinter import ttk

class SongRequestsPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Song Requests", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.placeholder = ttk.Label(self, text="No song requests loaded yet.", anchor="center")
        self.placeholder.grid(row=0, column=0, sticky="nsew")
