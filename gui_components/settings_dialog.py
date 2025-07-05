import tkinter as tk
from tkinter import ttk

LIST_KEYS = [
    "DISCORD_BOT_CHANNEL_IDS",
    "DISCORD_BOT_ADMIN_IDS",
    "DISCORD_LIVE_NOTIFICATION_ROLES"
]

LEFT_KEYS = [
    "DISCORD_TOKEN",
    "DISCORD_BOT_APP_ID",
    "DISCORD_BOT_ADMIN_IDS",
    "DISCORD_LIVE_NOTIFICATION_ROLES",
    "TRAKTOR_LOCATION",
    "TRAKTOR_COLLECTION_FILENAME",
    "TRAKTOR_BROADCAST_PORT",
    "NEW_SONGS_DAYS",
    "MAX_SONGS"
]

DESCRIPTIONS = {
    "DISCORD_TOKEN": "Discord bot token.",
    "DISCORD_BOT_APP_ID": "Discord bot application ID.",
    "DISCORD_BOT_CHANNEL_IDS": "Comma-separated list of channel IDs.",
    "DISCORD_BOT_ADMIN_IDS": "Comma-separated list of Discord user IDs.",
    "DISCORD_LIVE_NOTIFICATION_ROLES": "Comma-separated list of Discord roles.",
    "TRAKTOR_LOCATION": "Not the version folder itself.",
    "TRAKTOR_COLLECTION_FILENAME": "",
    "TRAKTOR_BROADCAST_PORT": "Restart listener to apply changes.",
    "NEW_SONGS_DAYS": "Number of days.",
    "MAX_SONGS": "Maximum number of songs to display.",
    "TIMEOUT": "For Song Requests.",
    "CONSOLE_PANEL_WIDTH": "Width of the console panel.",
    "COVER_SIZE": "Size (in pixels) of the GUI cover art.",
    "FADE_STYLE": "Transition style for Spout (fade/crossfade).",
    "FADE_FRAMES": "Number of frames for Spout transitions.",
    "FADE_DURATION": "Duration (in seconds) for Spout transitions.",
    "SPOUT_BORDER_PX": "Border size (in pixels) for Spout output.",
}

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings_dict, descriptions=None, on_save=None):
        super().__init__(parent)
        self.title("Settings")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)  # Allow horizontal and vertical resizing
        self.geometry("1125x675")  # Wider default size
        # Center the dialog over the parent window
        self.update_idletasks()
        if parent is not None:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            win_w = 1125
            win_h = 675
            x = parent_x + (parent_w // 2) - (win_w // 2)
            y = parent_y + (parent_h // 2) - (win_h // 2)
            self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.settings_dict = settings_dict.copy()
        self.entries = {}
        self.descriptions = descriptions or {}
        self.on_save = on_save
        # --- Save/Cancel buttons at the top ---
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=0, column=0, columnspan=4, pady=(12, 12), sticky="ew")
        save_btn = tk.Button(btn_frame, text="Save", command=self.save)
        save_btn.pack(side="left", padx=8)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side="left", padx=8)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        # --- Settings fields ---
        left_row = 1
        right_row = 1
        for key, value in self.settings_dict.items():
            col = 0 if key in LEFT_KEYS else 2
            row = left_row if col == 0 else right_row
            # Setting name
            label = tk.Label(self, text=key, font=("Arial", 10, "bold"))
            label.grid(row=row, column=col, sticky="w", padx=8, pady=(8, 0))
            # Description to the right of label (same column+1)
            desc = self.descriptions.get(key, "")
            if desc:
                desc_label = tk.Label(self, text=desc, font=("Arial", 8), fg="#666", wraplength=500, justify="left")
                desc_label.grid(row=row, column=col+1, sticky="w", padx=8, pady=(8, 0))
            row += 1
            # Input field directly below
            entry = tk.Entry(self, width=60)
            if key in LIST_KEYS and isinstance(value, list):
                entry.insert(0, ",".join(str(v) for v in value))
            else:
                entry.insert(0, str(value))
            entry.grid(row=row, column=col, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
            self.entries[key] = entry
            if col == 0:
                left_row = row + 1
            else:
                right_row = row + 1

    def save(self):
        import json
        import copy
        new_settings = copy.deepcopy(self.settings_dict)
        for key, entry in self.entries.items():
            val = entry.get()
            if key in LIST_KEYS:
                # Split by comma, strip whitespace, ignore empty
                items = [v.strip() for v in val.split(",") if v.strip()]
                new_settings[key] = items
            elif val.lower() in ("true", "false"):
                new_settings[key] = val.lower() == "true"
            else:
                try:
                    if "." in val:
                        new_settings[key] = float(val)
                    else:
                        new_settings[key] = int(val)
                except Exception:
                    new_settings[key] = val
        from config.settings import SETTINGS_PATH
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(new_settings, f, indent=2)
        from config.settings import Settings
        Settings.reload()
        if self.on_save:
            self.on_save(new_settings)
        self.destroy()

    def on_cancel(self):
        from utils.logger import info
        info("[SettingsDialog] User cancelled settings dialog.")
        self.destroy()
