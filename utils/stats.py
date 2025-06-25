"""
Stats management utilities for Traktor DJ NowPlaying Discord Bot
"""
import json
import os
from utils.logger import warning
from config.settings import Settings
from utils.events import emit

STATS_FILE = Settings.STATS_FILE
DEFAULT_GLOBAL_STATS = {
    "total_song_searches": 0,
    "session_song_searches": 0,
    "total_song_plays": 0,
    "session_song_plays": 0,
    "total_song_requests": 0,
    "session_song_requests": 0,
    # Add new stats here to have them auto-included in global reset
}
DEFAULT_SESSION_STATS = {
    "session_song_searches": 0,
    "session_song_plays": 0,
    "session_song_requests": 0,
    # Add new session stats here to have them auto-included in session reset
}

def load_stats(stats_file=STATS_FILE):
    if not os.path.exists(stats_file):
        save_stats(DEFAULT_GLOBAL_STATS, stats_file)
        return DEFAULT_GLOBAL_STATS.copy()
    try:
        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
        # Ensure all default keys exist
        for k, v in DEFAULT_GLOBAL_STATS.items():
            if k not in stats:
                stats[k] = v
        return stats
    except Exception as e:
        warning(f"⚠️ Error loading stats: {e}")
        return DEFAULT_GLOBAL_STATS.copy()

def save_stats(stats, stats_file=STATS_FILE):
    try:
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        warning(f"⚠️ Error saving stats: {e}")

def increment_stat(stat_name, amount=1, stats_file=STATS_FILE):
    stats = load_stats(stats_file)
    stats[stat_name] = stats.get(stat_name, 0) + amount
    save_stats(stats, stats_file)
    emit("stats_updated")
    return stats[stat_name]

def reset_session_stats(stats_file=STATS_FILE):
    """Reset all session stats in the stats file and persist."""
    stats = load_stats(stats_file)
    from utils.logger import info
    for k, v in DEFAULT_SESSION_STATS.items():
        if k in stats:
            old = stats[k]
            stats[k] = 0
            info(f"{k}: Reset to 0 (was {old})")
    save_stats(stats, stats_file)
    emit("stats_updated")
    return stats

def reset_global_stats(stats_file=STATS_FILE):
    """Reset all global stats to their default values and persist."""
    from utils.logger import info
    before = load_stats(stats_file)
    save_stats(DEFAULT_GLOBAL_STATS.copy(), stats_file)
    after = load_stats(stats_file)
    for k, v in DEFAULT_GLOBAL_STATS.items():
        if k in before:
            info(f"{k}: Reset to 0 (was {before[k]})")
    emit("stats_updated")
    return after
