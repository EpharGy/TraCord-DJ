"""
NowPlaying utilities for reading, clearing, and updating the NowPlaying config file.
"""
import os
import json
import shutil
from utils.logger import info, warning, error

def clear_nowplaying_track_history(config_path: str) -> bool:
    """
    Clear track history in the NowPlaying config.json file.
    Returns True if successful, False otherwise.
    """
    try:
        if not config_path or not os.path.exists(config_path):
            warning("❌ NowPlaying config file path is not set or does not exist.")
            return False
        info("🗑️ Clearing track history...")
        backup_path = config_path + ".bak"
        shutil.copyfile(config_path, backup_path)
        info(f"📁 Backup saved as {backup_path}")
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        fields_to_clear = ["title", "artist", "comment", "label", "album", "artwork"]
        if "currentTrack" in config:
            for field in fields_to_clear:
                if field in config["currentTrack"]:
                    config["currentTrack"][field] = ""
        if "trackList" in config:
            config["trackList"] = []
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
        info("✅ Track history cleared successfully")
        return True
    except Exception as e:
        error(f"❌ Error clearing track history: {e}")
        return False
