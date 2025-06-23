import tkinter as tk
from tkinter import ttk

class ControlsStatsPanel(ttk.Frame):
    def __init__(self, parent, button_texts, optimal_width, nowplaying_enabled, clear_log_cmd, refresh_collection_cmd, reset_global_stats_cmd, clear_track_history_cmd, on_stop_press, on_stop_release):
        super().__init__(parent)
        self.columnconfigure(0, weight=0)
        self.grid_columnconfigure(0, minsize=200)
        # Stop & Close button (now with red text)
        self.stop_button = ttk.Button(
            self,
            text=button_texts[0],
            width=optimal_width,
            state='normal',
            style="Red.TButton"
        )
        self.stop_button.bind('<Button-1>', on_stop_press)
        self.stop_button.bind('<ButtonRelease-1>', on_stop_release)
        self.stop_button.grid(row=0, column=0, pady=8)
        # Status section
        self.status_frame = ttk.LabelFrame(self, text="Status", padding="10")
        self.status_frame.grid(row=2, column=0, pady=(15, 10), sticky="ew")
        self.status_label = ttk.Label(self.status_frame, text="⚪ Bot Stopped")
        self.status_label.grid(row=0, column=0, sticky="w")
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
        self.stats_frame = ttk.LabelFrame(self, text="Collection Stats", padding="10")
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
        self.session_searches_label = ttk.Label(self.stats_frame, text="Song Searches (Session): 0")
        self.session_searches_label.grid(row=5, column=0, sticky="w")
        self.total_searches_label = ttk.Label(self.stats_frame, text="Total Song Searches: 0")
        self.total_searches_label.grid(row=6, column=0, sticky="w")
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
        # Clear NP track info button (only if NowPlaying is enabled)
        if nowplaying_enabled:
            self.clear_history_button = ttk.Button(
                self,
                text=button_texts[3],
                command=clear_track_history_cmd,
                width=optimal_width
            )
            self.clear_history_button.grid(row=8, column=0, pady=8)

    @staticmethod
    def calculate_optimal_button_width(button_texts):
        max_length = 0
        for text in button_texts:
            text_length = len(text)
            max_length = max(max_length, text_length)
        optimal_width = max_length
        return max(optimal_width, 12)

    @staticmethod
    def calculate_controls_frame_width(nowplaying_enabled):
        max_width = 0
        button_texts = [
            "🛑 Stop & Close",
            "🗑️ Clear Log", 
            "🔄 Refresh Collection & Stats"
        ]
        if nowplaying_enabled:
            button_texts.append("🧹 Clear NP Track Info")
        button_width = ControlsStatsPanel.calculate_optimal_button_width(button_texts)
        max_width = max(max_width, button_width)
        stats_texts = [
            "Songs: 999,999",
            "New Songs: 9,999"
        ]
        for text in stats_texts:
            max_width = max(max_width, len(text))
        return max_width + 2

    def update_controls_frame_sizing(self, nowplaying_enabled):
        try:
            optimal_width = ControlsStatsPanel.calculate_controls_frame_width(nowplaying_enabled)
            pixel_width = optimal_width * 7
            self.grid_columnconfigure(0, minsize=pixel_width)
        except Exception as e:
            from utils.logger import error
            error(f"Error updating controls frame sizing: {e}")

# Add a custom style for Red.TButton
from tkinter import ttk
style = ttk.Style()
try:
    style.configure("Red.TButton", foreground="#b22222")  # Firebrick red text
except Exception:
    pass
