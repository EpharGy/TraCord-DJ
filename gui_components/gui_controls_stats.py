import tkinter as tk
from tkinter import ttk
from typing import Optional

class ControlsStatsPanel(ttk.LabelFrame):
    STANDARD_PADY = 4
    def __init__(self, parent, button_texts, optimal_width, clear_log_cmd, refresh_collection_cmd, reset_global_stats_cmd, clear_track_history_cmd, on_stop_press, on_stop_release, on_toggle_traktor_listener=lambda: None):
        super().__init__(parent, text="Controls & Stats", padding=self.STANDARD_PADY)
        self.columnconfigure(0, weight=0)
        self.grid_columnconfigure(0, minsize=100)
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
        self.stop_button.grid(row=0, column=0, pady=self.STANDARD_PADY)
        # Status section
        self.status_frame = ttk.LabelFrame(self, text="Status", padding=self.STANDARD_PADY)
        self.status_frame.grid(row=1, column=0, pady=self.STANDARD_PADY, sticky="ew")
        self.status_label = ttk.Label(self.status_frame, text="⚪ Bot Stopped")
        self.status_label.grid(row=0, column=0, sticky="w")  # No padding
        # Traktor Listener status label
        self.traktor_listener_status_label = ttk.Label(self.status_frame, text="🔴 Listener Off")
        self.traktor_listener_status_label.grid(row=1, column=0, sticky="w")  # No padding
        # Bot info section
        self.info_frame = ttk.LabelFrame(self, text="Bot Information", padding=self.STANDARD_PADY)
        self.info_frame.grid(row=2, column=0, pady=self.STANDARD_PADY, sticky="ew")
        self.bot_name_label = ttk.Label(self.info_frame, text="Name: Not connected")
        self.bot_name_label.grid(row=0, column=0, sticky="w")  # No padding
        self.bot_id_label = ttk.Label(self.info_frame, text="ID: Not connected")
        self.bot_id_label.grid(row=1, column=0, sticky="w")  # No padding
        self.commands_label = ttk.Label(self.info_frame, text="Commands: Not loaded")
        self.commands_label.grid(row=2, column=0, sticky="w")  # No padding
        # Statistics section
        self.stats_frame = ttk.LabelFrame(self, text="Stats", padding=self.STANDARD_PADY)
        self.stats_frame.grid(row=3, column=0, pady=self.STANDARD_PADY, sticky="ew")
        self.import_title_label = ttk.Label(self.stats_frame, text="Traktor Import:", font=("Arial", 9, "bold"))
        self.import_title_label.grid(row=0, column=0, sticky="w")  # No padding
        self.import_date_label = ttk.Label(self.stats_frame, text="Loading...", font=("Arial", 8))
        self.import_date_label.grid(row=1, column=0, sticky="w", padx=(10, 0))  # No padding
        self.import_time_label = ttk.Label(self.stats_frame, text="", font=("Arial", 8))
        self.import_time_label.grid(row=2, column=0, sticky="w", padx=(10, 0))  # No padding
        self.songs_label = ttk.Label(self.stats_frame, text="Songs: Loading...")
        self.songs_label.grid(row=3, column=0, sticky="w")
        self.new_songs_label = ttk.Label(self.stats_frame, text="New Songs: Loading...")
        self.new_songs_label.grid(row=4, column=0, sticky="w", pady=(0, self.STANDARD_PADY))
        # Session Stats heading
        self.session_stats_heading = ttk.Label(self.stats_frame, text="Session Stats", font=("Arial", 9, "bold"))
        self.session_stats_heading.grid(row=5, column=0, sticky="w")
        self.session_searches_label = ttk.Label(self.stats_frame, text="Song Searches: 0")
        self.session_searches_label.grid(row=6, column=0, sticky="w")
        self.session_requests_label = ttk.Label(self.stats_frame, text="Song Requests: 0")
        self.session_requests_label.grid(row=7, column=0, sticky="w")
        self.session_plays_label = ttk.Label(self.stats_frame, text="Songs Played: 0")
        self.session_plays_label.grid(row=8, column=0, sticky="w", pady=(0, self.STANDARD_PADY))
        # Space before total stats
        self.total_stats_heading = ttk.Label(self.stats_frame, text="Total Stats", font=("Arial", 9, "bold"))
        self.total_stats_heading.grid(row=9, column=0, sticky="w")
        self.total_searches_label = ttk.Label(self.stats_frame, text="Song Searches: 0")
        self.total_searches_label.grid(row=10, column=0, sticky="w")
        self.total_requests_label = ttk.Label(self.stats_frame, text="Song Requests: 0")
        self.total_requests_label.grid(row=11, column=0, sticky="w")
        self.total_plays_label = ttk.Label(self.stats_frame, text="Songs Played: 0")
        self.total_plays_label.grid(row=12, column=0, sticky="w", pady=(0, self.STANDARD_PADY))
        # Clear log button
        self.clear_button = ttk.Button(
            self,
            text=button_texts[1],
            command=clear_log_cmd,
            width=optimal_width
        )
        self.clear_button.grid(row=5, column=0, pady=self.STANDARD_PADY)
        # Refresh session stats button
        self.refresh_button = ttk.Button(
            self,
            text="🔄 Reset Session Stats",
            command=refresh_collection_cmd,
            width=optimal_width
        )
        self.refresh_button.grid(row=6, column=0, pady=self.STANDARD_PADY)
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
        self.reset_global_button.grid(row=7, column=0, pady=self.STANDARD_PADY)
        # Settings button (above Clear Log)
        self.settings_button = ttk.Button(
            self,
            text="⚙️ Settings",
            width=optimal_width,
            command=lambda: None
        )
        self.settings_button.grid(row=4, column=0, pady=self.STANDARD_PADY)

    @staticmethod
    def calculate_optimal_button_width(button_texts):
       # Remove Clear NP Track Info from width calculation
        filtered = [t for t in button_texts]
        max_length = 0
        for text in filtered:
            text_length = len(text)
            max_length = max(max_length, text_length)
        optimal_width = max(max_length - 6 , 10)
        # optimal_width = max_length
        # optimal_width = 3
        return optimal_width

    @staticmethod
    def calculate_controls_frame_width():
        max_width = 0
        button_texts = [
            "🛑 Stop All & Close",
            "🗑️ Clear Log", 
            "🔄 Reset Session Stats"
        ]
        button_width = ControlsStatsPanel.calculate_optimal_button_width(button_texts)
        max_width = max(max_width, button_width)
        stats_texts = [
            "Songs: 999,99",
            "New Songs: 9,99"
        ]
        for text in stats_texts:
            max_width = max(max_width, len(text))
        return max_width + 2 #+extra padding for aesthetics

    def update_controls_frame_sizing(self):
        try:
            optimal_width = ControlsStatsPanel.calculate_controls_frame_width()
            pixel_width = optimal_width * 8 # 8 pixels per character is a common approximation 
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

    def update_stats_labels(self, stats):
        self.session_searches_label.config(text=f"Song Searches: {stats.get('session_song_searches', 0)}")
        self.total_searches_label.config(text=f"Total Song Searches: {stats.get('total_song_searches', 0)}")
        self.session_requests_label.config(text=f"Song Requests: {stats.get('session_song_requests', 0)}")
        self.total_requests_label.config(text=f"Total Song Requests: {stats.get('total_song_requests', 0)}")
        self.session_plays_label.config(text=f"Songs Played: {stats.get('session_song_plays', 0)}")
        self.total_plays_label.config(text=f"Total Songs Played: {stats.get('total_song_plays', 0)}")

    def set_settings_command(self, cmd):
        self.settings_button.config(command=cmd)

    def set_overlay_command(self, cmd):
        pass  # No longer needed, overlay button is now in NowPlayingPanel

# Add a custom style for Red.TButton
from tkinter import ttk
style = ttk.Style()
try:
    style.configure("Red.TButton", foreground="#b22222")  # Firebrick red text
except Exception:
    pass
