import tkinter as tk
from tkinter import ttk
from typing import Optional

class ControlsStatsPanel(ttk.LabelFrame):
    def __init__(self, parent, button_texts, optimal_width, clear_log_cmd, refresh_collection_cmd, reset_global_stats_cmd, clear_track_history_cmd, on_stop_press, on_stop_release, on_toggle_traktor_listener=lambda: None):
        super().__init__(parent, text="Controls & Stats", padding="8")
        self.columnconfigure(0, weight=0)
        self.grid_columnconfigure(0, minsize=200)
        # Stop All & Close button (now with red text)
        self.stop_button = ttk.Button(
            self,
            text="🛑 Stop All & Close",
            width=optimal_width,
            state='normal',
            style="Red.TButton"
        )
        self.stop_button.bind('<Button-1>', on_stop_press)
        self.stop_button.bind('<ButtonRelease-1>', on_stop_release)
        self.stop_button.grid(row=0, column=0, pady=8)
        # Toggle Traktor Listener button (starts in Turn On state)
        self.toggle_traktor_listener_button = ttk.Button(
            self,
            text="⭕ Turn On Traktor Listener",
            width=optimal_width,
            command=on_toggle_traktor_listener,
            style="TButton"
        )
        self.toggle_traktor_listener_button.grid(row=1, column=0, pady=(0, 8))
        # Status section
        self.status_frame = ttk.LabelFrame(self, text="Status", padding="10")
        self.status_frame.grid(row=2, column=0, pady=(15, 10), sticky="ew")
        self.status_label = ttk.Label(self.status_frame, text="⚪ Bot Stopped")
        self.status_label.grid(row=0, column=0, sticky="w")
        # Traktor Listener status label
        self.traktor_listener_status_label = ttk.Label(self.status_frame, text="🔴 Traktor Listener Offline")
        self.traktor_listener_status_label.grid(row=1, column=0, sticky="w")
        # Bot info section
        self.info_frame = ttk.LabelFrame(self, text="Bot Information", padding="10")
        self.info_frame.grid(row=3, column=0, pady=10, sticky="ew")
        self.bot_name_label = ttk.Label(self.info_frame, text="Name: Not connected")
        self.bot_name_label.grid(row=0, column=0, sticky="w")
        self.bot_id_label = ttk.Label(self.info_frame, text="ID: Not connected")
        self.bot_id_label.grid(row=1, column=0, sticky="w")
        self.commands_label = ttk.Label(self.info_frame, text="Commands: Not loaded")
        self.commands_label.grid(row=2, column=0, sticky="w")
        # Statistics section
        self.stats_frame = ttk.LabelFrame(self, text="Stats", padding="10")
        self.stats_frame.grid(row=4, column=0, pady=10, sticky="ew")
        self.import_title_label = ttk.Label(self.stats_frame, text="Traktor Import:", font=("Arial", 9, "bold"))
        self.import_title_label.grid(row=0, column=0, sticky="w")
        self.import_date_label = ttk.Label(self.stats_frame, text="Loading...", font=("Arial", 8))
        self.import_date_label.grid(row=1, column=0, sticky="w", padx=(10, 0))
        self.import_time_label = ttk.Label(self.stats_frame, text="", font=("Arial", 8))
        self.import_time_label.grid(row=2, column=0, sticky="w", padx=(10, 0))
        self.songs_label = ttk.Label(self.stats_frame, text="Songs: Loading...")
        self.songs_label.grid(row=3, column=0, sticky="w", pady=(5, 0))
        self.new_songs_label = ttk.Label(self.stats_frame, text="New Songs: Loading...")
        self.new_songs_label.grid(row=4, column=0, sticky="w")
        # Session Stats heading
        self.session_stats_heading = ttk.Label(self.stats_frame, text="Session Stats", font=("Arial", 9, "bold"))
        self.session_stats_heading.grid(row=5, column=0, sticky="w", pady=(10, 0))
        self.session_searches_label = ttk.Label(self.stats_frame, text="Song Searches: 0")
        self.session_searches_label.grid(row=6, column=0, sticky="w")
        self.session_requests_label = ttk.Label(self.stats_frame, text="Song Requests: 0")
        self.session_requests_label.grid(row=7, column=0, sticky="w")
        self.session_plays_label = ttk.Label(self.stats_frame, text="Songs Played: 0")
        self.session_plays_label.grid(row=8, column=0, sticky="w")
        # Space before total stats
        self.total_stats_heading = ttk.Label(self.stats_frame, text="Total Stats", font=("Arial", 9, "bold"))
        self.total_stats_heading.grid(row=9, column=0, sticky="w", pady=(10, 0))
        self.total_searches_label = ttk.Label(self.stats_frame, text="Song Searches: 0")
        self.total_searches_label.grid(row=10, column=0, sticky="w")
        self.total_requests_label = ttk.Label(self.stats_frame, text="Song Requests: 0")
        self.total_requests_label.grid(row=11, column=0, sticky="w")
        self.total_plays_label = ttk.Label(self.stats_frame, text="Songs Played: 0")
        self.total_plays_label.grid(row=12, column=0, sticky="w")
        # Clear log button
        self.clear_button = ttk.Button(
            self,
            text=button_texts[1],
            command=clear_log_cmd,
            width=optimal_width
        )
        self.clear_button.grid(row=5, column=0, pady=(15, 8))
        # Refresh session stats button
        self.refresh_button = ttk.Button(
            self,
            text="🔄 Refresh Session Stats",
            command=refresh_collection_cmd,
            width=optimal_width
        )
        self.refresh_button.grid(row=6, column=0, pady=8)
        # Reset global stats button
        self.reset_global_button = ttk.Button(
            self,
            text="🧹 Reset Global Stats",
            command=reset_global_stats_cmd,
            width=optimal_width
        )
        try:
            self.reset_global_button.configure(
                style="Red.TButton"
            )
        except Exception:
            pass
        self.reset_global_button.grid(row=7, column=0, pady=8)

    @staticmethod
    def calculate_optimal_button_width(button_texts):
        # Remove Clear NP Track Info from width calculation
        filtered = [t for t in button_texts if t != "🧹 Clear NP Track Info"]
        max_length = 0
        for text in filtered:
            text_length = len(text)
            max_length = max(max_length, text_length)
        optimal_width = max(max_length, 12)
        return optimal_width

    @staticmethod
    def calculate_controls_frame_width():
        max_width = 0
        button_texts = [
            "🛑 Stop & Close",
            "🗑️ Clear Log", 
            "🔄 Refresh Collection & Stats"
        ]
        button_width = ControlsStatsPanel.calculate_optimal_button_width(button_texts)
        max_width = max(max_width, button_width)
        stats_texts = [
            "Songs: 999,99",
            "New Songs: 9,99"
        ]
        for text in stats_texts:
            max_width = max(max_width, len(text))
        return max_width + 2

    def update_controls_frame_sizing(self):
        try:
            optimal_width = ControlsStatsPanel.calculate_controls_frame_width()
            pixel_width = optimal_width * 7
            self.grid_columnconfigure(0, minsize=pixel_width)
        except Exception as e:
            from utils.logger import error
            error(f"Error updating controls frame sizing: {e}")

    def set_traktor_listener_status(self, status: str, foreground: Optional[str] = None):
        """Update the Traktor Listener status indicator and color."""
        if foreground is not None:
            self.traktor_listener_status_label.config(text=status, foreground=foreground)
        else:
            self.traktor_listener_status_label.config(text=status)

    def set_traktor_toggle_button(self, is_on: bool):
        """Update the toggle button text and style based on listener state."""
        if is_on:
            self.toggle_traktor_listener_button.config(text="❌ Turn Off Traktor Listener", style="Red.TButton")
        else:
            self.toggle_traktor_listener_button.config(text="⭕ Turn On Traktor Listener", style="TButton")

# Add a custom style for Red.TButton
from tkinter import ttk
style = ttk.Style()
try:
    style.configure("Red.TButton", foreground="#b22222")  # Firebrick red text
except Exception:
    pass
