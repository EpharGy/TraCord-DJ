import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
from copy import deepcopy
from utils.events import subscribe
from utils.helpers import update_request_numbers
from utils.logger import info
from config.settings import Settings
import functools

SONG_REQUESTS_FILE = Settings.SONG_REQUESTS_FILE

class SongRequestsPanel(ttk.LabelFrame):
    _instance = None  # Singleton instance for event-based access
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Song Requests", padding="8", *args, **kwargs)
        SongRequestsPanel._instance = self  # Set the singleton instance
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Topbar (buttons) does not expand
        # --- Top button bar ---
        topbar = ttk.Frame(self)
        topbar.grid(row=0, column=0, sticky="nw", pady=(0, 8))
        topbar.columnconfigure(0, weight=0)
        topbar.columnconfigure(1, weight=0)
        # Remove All button
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="#b22222")  # Use same Firebrick red as Stop & Close
        self.remove_all_btn = ttk.Button(
            topbar, text="❌ Remove All", command=self.remove_all_requests, style="Danger.TButton"
        )
        self.remove_all_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")
        # Toggle Clean List button
        self.clean_list_btn = ttk.Button(
            topbar, text="⤴ Open", command=self.toggle_clean_list_window
        )
        self.clean_list_btn.grid(row=0, column=1, sticky="w")
        # --- End top button bar ---
        self.requests = []
        self._last_requests = []
        self.clean_list_window = None
        self.load_requests()
        subscribe("song_request_added", self.handle_song_added)
        subscribe("song_request_deleted", self.handle_song_deleted)
        # Subscribe popout refresh to events
        subscribe("song_request_added", lambda _: self.refresh_clean_list_window())
        subscribe("song_request_deleted", lambda _: self.refresh_clean_list_window())


    def get_request_id(self, req):
        # Use User, Song, Date for unique ID (not RequestNumber)
        return f"{req.get('User','')}|{req.get('Song','')}|{req.get('Date','')}"

    def handle_song_added(self, new_request):
        if new_request:
            self.load_requests()

    def handle_song_deleted(self, _):
        try:
            with open(SONG_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                current_requests = json.load(f)
        except Exception:
            current_requests = []
        self.requests = current_requests
        self.load_requests()

    def load_requests(self):
        try:
            with open(SONG_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                self.requests = json.load(f)
        except Exception:
            self.requests = []
        self._last_requests = deepcopy(self.requests)

    def remove_request(self, idx):
        if 0 <= idx < len(self.requests):
            removed = self.requests[idx]
            del self.requests[idx]
            update_request_numbers(self.requests)
            try:
                with open(SONG_REQUESTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.requests, f, indent=4, ensure_ascii=False)
            except Exception:
                pass
            info(f"{removed.get('Song','')} removed from Song Requests")
            self.load_requests()
            self.refresh_clean_list_window()

    def refresh_requests_panel(self):
        self.load_requests()

    def remove_all_requests(self):
        if not self.requests:
            return
        if not messagebox.askyesno("Confirm Remove All", "Are you sure you want to remove ALL song requests? This cannot be undone."):
            return
        self.requests.clear()
        try:
            with open(SONG_REQUESTS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4, ensure_ascii=False)
        except Exception:
            pass
        info("All song requests removed")
        self.load_requests()
        self.refresh_clean_list_window()

    def toggle_clean_list_window(self):
        if self.clean_list_window and tk.Toplevel.winfo_exists(self.clean_list_window):
            self.clean_list_window.destroy()
            self.clean_list_window = None
            self.clean_list_btn.config(text="⤴ Open")
            return
        self.clean_list_window = tk.Toplevel(self)
        self.clean_list_window.title("Song Requests")
        # Set custom icon for the popup window
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app_icon.ico')
        if os.path.exists(icon_path):
            try:
                self.clean_list_window.iconbitmap(icon_path)
            except Exception:
                pass
        self.clean_list_window.geometry("750x500")
        self.clean_list_window.resizable(True, True)
        self.clean_list_window.attributes("-topmost", True)
        self.render_clean_list_window()
        self.clean_list_btn.config(text="⤵ Close")

    def refresh_clean_list_window(self):
        if self.clean_list_window and tk.Toplevel.winfo_exists(self.clean_list_window):
            self.render_clean_list_window()

    def render_clean_list_window(self):
        if not self.clean_list_window:
            return
        for widget in self.clean_list_window.winfo_children():
            widget.destroy()
        frame = ttk.Frame(self.clean_list_window, padding=20)
        frame.pack(fill="both", expand=True)
        style = ttk.Style()
        sfontsize = 10
        spadwidth = 2
        style.configure("SongRemove.TButton", foreground="#b22222", font=("Segoe UI", sfontsize, "bold"))
        max_user_len = max((len(req.get('User', '')) for req in self.requests), default=8)
        max_num_len = max((len(f"#{req.get('RequestNumber', idx+1)}") for idx, req in enumerate(self.requests)), default=2)
        if not self.requests:
            label = ttk.Label(frame, text="No songs in the list.", anchor="center")
            label.pack(fill="both", expand=True)
        else:
            for idx, req in enumerate(self.requests):
                row_frame = ttk.Frame(frame)
                row_frame.pack(fill="x", pady=2, anchor="w")
                req_num = req.get('RequestNumber', idx+1)
                user = req.get('User', 'Unknown')
                song = req.get('Song', '')
                btn_remove = ttk.Button(row_frame, text="❌", width=3, style="SongRemove.TButton", command=functools.partial(self.remove_request, idx))
                btn_remove.pack(side="left", padx=(0, spadwidth))
                lbl_num = ttk.Label(row_frame, text=f"#{req_num}", width=max_num_len, anchor="w", font=("Segoe UI", sfontsize, "bold"))
                lbl_num.pack(side="left", padx=(0, spadwidth))
                lbl_user = ttk.Label(row_frame, text=user, width=max_user_len, anchor="w", justify="left", font=("Segoe UI", sfontsize))
                lbl_user.pack(side="left", padx=(0, spadwidth))
                lbl_song = ttk.Label(row_frame, text=song, anchor="w", justify="left", font=("Segoe UI", sfontsize), wraplength=600)
                lbl_song.pack(side="left", padx=(0, 0))

    @staticmethod
    def normalize_string(artist: str, title: str) -> str:
        """Normalize song data for comparison."""
        return f"{artist.strip().lower()} - {title.strip().lower()}"

