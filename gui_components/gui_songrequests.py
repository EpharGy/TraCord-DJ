import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
from copy import deepcopy
from utils.events import subscribe
from utils.song_request_highlight import highlighter
from utils.helpers import update_request_numbers
from utils.logger import info

SONG_REQUESTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'song_requests.json')

class SongRequestsPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Song Requests", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        # --- Top button bar ---
        topbar = ttk.Frame(self)
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        topbar.columnconfigure(0, weight=0)
        topbar.columnconfigure(1, weight=0)
        # Remove All button
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="#b22222")  # Use same Firebrick red as Stop & Close
        self.remove_all_btn = ttk.Button(
            topbar, text="❌ Remove All Song Requests", command=self.remove_all_requests, style="Danger.TButton"
        )
        self.remove_all_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")
        # Toggle Clean List button
        self.clean_list_btn = ttk.Button(
            topbar, text="⤴ Pop up song list", command=self.toggle_clean_list_window
        )
        self.clean_list_btn.grid(row=0, column=1, sticky="w")
        # --- End top button bar ---
        self.requests_frame = ttk.Frame(self)
        self.requests_frame.grid(row=1, column=0, sticky="nsew")
        self.requests_frame.columnconfigure(1, weight=1)
        # Ensure the main panel expands vertically, but buttons stay at the top
        self.rowconfigure(0, weight=0)  # Topbar (buttons) does not expand
        self.rowconfigure(1, weight=1)  # requests_frame (list) expands
        self.requests = []
        self._row_widgets = {}  # Track row widgets by request id
        self._pending_highlights = set()
        self._last_requests = []
        self._deleted_rows = {}  # Track deleted rows and their timers by ID
        self.clean_list_window = None
        self.load_requests()
        subscribe("song_request_added", self.handle_song_added)
        subscribe("song_request_deleted", self.handle_song_deleted)

    def get_request_id(self, req):
        # Use User, Song, Date for unique ID (not RequestNumber)
        return f"{req.get('User','')}|{req.get('Song','')}|{req.get('Date','')}"

    def handle_song_added(self, new_request):
        if new_request:
            req_id = self.get_request_id(new_request)
            self._pending_highlights.add((req_id, 'add'))
        self.load_requests()

    def handle_song_deleted(self, _):
        try:
            with open(SONG_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                current_requests = json.load(f)
        except Exception:
            current_requests = []
        prev_ids = {self.get_request_id(req) for req in self._last_requests}
        curr_ids = {self.get_request_id(req) for req in current_requests}
        deleted_ids = prev_ids - curr_ids
        # Add new deleted rows to dict, start timer for each
        for req in self._last_requests:
            req_id = self.get_request_id(req)
            if req_id in deleted_ids and req_id not in self._deleted_rows:
                self._deleted_rows[req_id] = {'req': req, 'timer': self.requests_frame.after(5000, lambda rid=req_id: self._remove_single_deleted_row(rid))}
        self.requests = current_requests
        self.load_requests(render_deleted=True)

    def load_requests(self, render_deleted=False):
        self.clear_requests()
        try:
            with open(SONG_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                self.requests = json.load(f)
        except Exception:
            self.requests = []
        self._last_requests = deepcopy(self.requests)
        # Calculate max user name length for dynamic width
        max_user_len = max((len(req.get('User', '')) for req in self.requests), default=8)
        # Estimate width in pixels (roughly 8px per char, min 80)
        user_col_width = max(5, max_user_len * 8)
        self.requests_frame.columnconfigure(1, weight=0, minsize=user_col_width)
        self.requests_frame.columnconfigure(2, weight=1)
        if not self.requests and not (render_deleted and self._deleted_rows):
            placeholder = ttk.Label(self.requests_frame, text="No song requests loaded yet.", anchor="center")
            placeholder.grid(row=0, column=0, columnspan=3, sticky="nsew")
        else:
            self._row_widgets.clear()
            for idx, req in enumerate(self.requests):
                req_id = self.get_request_id(req)
                # If this row is pending green highlight, don't show tick
                if (req_id, 'add') in self._pending_highlights:
                    self.add_request_row(idx, req, force_green=True)
                else:
                    self.add_request_row(idx, req)
            # Render all deleted rows in red if needed
            if render_deleted and self._deleted_rows:
                base_idx = len(self.requests)
                for i, (req_id, data) in enumerate(self._deleted_rows.items()):
                    self.add_request_row(base_idx + i, data['req'], force_red=True)

    def clear_requests(self):
        for widget in self.requests_frame.winfo_children():
            widget.destroy()

    def add_request_row(self, idx, req, force_red=False, force_green=False):
        req_id = self.get_request_id(req)
        # Only show the ✔ button for live requests, not deleted or newly added (green) ones
        if not force_red and not force_green:
            btn = ttk.Button(self.requests_frame, text="✔", width=3, command=lambda i=idx: self.remove_request(i))
            btn.grid(row=idx, column=0, padx=(0, 8), pady=4)
        name = ttk.Label(self.requests_frame, text=req.get('User', 'Unknown'), anchor="w")
        name.grid(row=idx, column=1, sticky="w", padx=(0, 8))
        song = ttk.Label(self.requests_frame, text=req.get('Song', ''), anchor="w")
        song.grid(row=idx, column=2, sticky="ew")
        self._row_widgets[req_id] = (name, song)
        if force_red:
            for w in (name, song):
                w.configure(foreground='red')
        if force_green:
            for w in (name, song):
                w.configure(foreground='green')
        # Highlight if pending
        for pending_id, action in list(self._pending_highlights):
            if req_id == pending_id and action == 'add':
                self.highlight_row(req_id, 'green', remove_after=False, no_tick=True)
                self._pending_highlights.remove((pending_id, action))

    def highlight_row(self, req_id, color, remove_after=False, no_tick=False):
        widgets = self._row_widgets.get(req_id)
        if widgets:
            for w in widgets:
                w.configure(foreground=color)
            def revert(_):
                if remove_after:
                    for w in widgets:
                        w.grid_remove()
                else:
                    for w in widgets:
                        w.configure(foreground='black')
                    # If this was a green highlight (add), re-render row with tickbox
                    if color == 'green':
                        # Find the row index
                        for idx, req in enumerate(self.requests):
                            if self.get_request_id(req) == req_id:
                                # Remove current widgets
                                for w in widgets:
                                    w.grid_remove()
                                # Re-add row with tickbox
                                self.add_request_row(idx, req)
                                break
            highlighter.highlight(req_id, revert, duration=5, color=color)

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

    def refresh_requests_panel(self):
        self.load_requests()

    def _remove_single_deleted_row(self, req_id):
        # Remove a single deleted row from the GUI and dict
        data = self._deleted_rows.pop(req_id, None)
        widgets = self._row_widgets.get(req_id)
        if widgets:
            for w in widgets:
                w.grid_remove()
        # Only reload if no more deleted rows are pending
        if not self._deleted_rows:
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

    def toggle_clean_list_window(self):
        if self.clean_list_window and tk.Toplevel.winfo_exists(self.clean_list_window):
            self.clean_list_window.destroy()
            self.clean_list_window = None
            self.clean_list_btn.config(text="⤴ Pop up song list")
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
        self.clean_list_window.geometry("500x600")
        self.clean_list_window.resizable(True, True)
        self.clean_list_window.attributes("-topmost", True)
        frame = ttk.Frame(self.clean_list_window, padding=20)
        frame.pack(fill="both", expand=True)
        song_titles = [req.get('Song', '') for req in self.requests]
        if not song_titles:
            label = ttk.Label(frame, text="No songs in the list.", anchor="center")
            label.pack(fill="both", expand=True)
        else:
            for song in song_titles:
                label = ttk.Label(frame, text=song, anchor="w", font=("Segoe UI", 14))
                label.pack(fill="x", pady=2, anchor="w")
        self.clean_list_btn.config(text="⤵ Close pop up")
