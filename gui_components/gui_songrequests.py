import tkinter as tk
from tkinter import ttk
import json
import os

SONG_REQUESTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'song_requests.json')

class SongRequestsPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Song Requests", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.requests_frame = ttk.Frame(self)
        self.requests_frame.grid(row=0, column=0, sticky="nsew")
        self.requests_frame.columnconfigure(1, weight=1)
        self.requests = []
        self.load_requests()

    def load_requests(self):
        self.clear_requests()
        try:
            with open(SONG_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                self.requests = json.load(f)
        except Exception:
            self.requests = []
        # Calculate max user name length for dynamic width
        max_user_len = max((len(req.get('User', '')) for req in self.requests), default=8)
        # Estimate width in pixels (roughly 8px per char, min 80)
        user_col_width = max(5, max_user_len * 8)
        self.requests_frame.columnconfigure(1, weight=0, minsize=user_col_width)
        self.requests_frame.columnconfigure(2, weight=1)
        if not self.requests:
            placeholder = ttk.Label(self.requests_frame, text="No song requests loaded yet.", anchor="center")
            placeholder.grid(row=0, column=0, columnspan=3, sticky="nsew")
        else:
            for idx, req in enumerate(self.requests):
                self.add_request_row(idx, req)

    def clear_requests(self):
        for widget in self.requests_frame.winfo_children():
            widget.destroy()

    def add_request_row(self, idx, req):
        btn = ttk.Button(self.requests_frame, text="✔", width=3, command=lambda i=idx: self.remove_request(i))
        btn.grid(row=idx, column=0, padx=(0, 8), pady=4)
        name = ttk.Label(self.requests_frame, text=req.get('User', 'Unknown'), anchor="w")
        name.grid(row=idx, column=1, sticky="w", padx=(0, 8))
        song = ttk.Label(self.requests_frame, text=req.get('Song', ''), anchor="w")
        song.grid(row=idx, column=2, sticky="ew")
        # Column weights set in load_requests

    def remove_request(self, idx):
        if 0 <= idx < len(self.requests):
            del self.requests[idx]
            try:
                with open(SONG_REQUESTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.requests, f, indent=4, ensure_ascii=False)
            except Exception:
                pass
            self.load_requests()

    def refresh_requests_panel(self):
        self.load_requests()
