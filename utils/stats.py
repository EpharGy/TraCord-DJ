"""
Stats management utilities for Traktor DJ NowPlaying Discord Bot
"""
import json
import os
import tempfile
from typing import Dict, Any

from config.settings import Settings
from tracord.core.events import EventTopic, emit_event
from utils.logger import get_logger

logger = get_logger(__name__)

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

def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass


def load_stats(stats_file: str = STATS_FILE) -> Dict[str, Any]:
    """Load stats from disk. If missing or unreadable, return defaults (no overwrite)."""
    if not os.path.exists(stats_file):
        return DEFAULT_GLOBAL_STATS.copy()
    try:
        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
        if not isinstance(stats, dict):
            raise ValueError("stats.json is not a JSON object")
        # Ensure all default keys exist
        for k, v in DEFAULT_GLOBAL_STATS.items():
            if k not in stats:
                stats[k] = v
        return stats
    except Exception as e:
        logger.warning(f"⚠️ Error loading stats: {e}")
        return DEFAULT_GLOBAL_STATS.copy()

def save_stats(stats: Dict[str, Any], stats_file: str = STATS_FILE) -> None:
    try:
        _ensure_dir(stats_file)
        from utils.helpers import safe_write_json
        safe_write_json(stats_file, stats, indent=2, ensure_ascii=False, retries=3, backoff=0.1)
    except Exception as e:
        logger.warning(f"⚠️ Error saving stats: {e}")


def ensure_stats_initialized(stats_file: str = STATS_FILE) -> None:
    """Create a default stats file on first launch if it doesn't exist."""
    if not os.path.exists(stats_file):
        save_stats(DEFAULT_GLOBAL_STATS.copy(), stats_file)

def increment_stat(stat_name, amount=1, stats_file=STATS_FILE):
    stats = load_stats(stats_file)
    stats[stat_name] = stats.get(stat_name, 0) + amount
    save_stats(stats, stats_file)
    emit_event(EventTopic.STATS_UPDATED)
    return stats[stat_name]

def reset_session_stats(stats_file=STATS_FILE):
    """Reset all session stats in the stats file and persist."""
    stats = load_stats(stats_file)
    for k, v in DEFAULT_SESSION_STATS.items():
        if k in stats:
            old = stats[k]
            stats[k] = 0
            logger.info(f"{k}: Reset to 0 (was {old})")
    save_stats(stats, stats_file)
    emit_event(EventTopic.STATS_UPDATED)
    return stats

def reset_global_stats(stats_file=STATS_FILE):
    """Reset all global stats to their default values and persist."""
    before = load_stats(stats_file)
    save_stats(DEFAULT_GLOBAL_STATS.copy(), stats_file)
    after = load_stats(stats_file)
    for k, v in DEFAULT_GLOBAL_STATS.items():
        if k in before:
            logger.info(f"{k}: Reset to 0 (was {before[k]})")
    emit_event(EventTopic.STATS_UPDATED)
    return after


def increment_song_play(stats_file: str = STATS_FILE) -> Dict[str, Any]:
    """Atomically increment both total and session song play counters and emit once.

    This avoids two back-to-back writes (and two events) that can race a concurrent
    reader during the brief file truncation window.
    """
    stats = load_stats(stats_file)
    stats["total_song_plays"] = stats.get("total_song_plays", 0) + 1
    stats["session_song_plays"] = stats.get("session_song_plays", 0) + 1
    save_stats(stats, stats_file)
    emit_event(EventTopic.STATS_UPDATED)
    return stats


def increment_song_search(stats_file: str = STATS_FILE) -> Dict[str, Any]:
    """Atomically increment both total and session song search counters and emit once."""
    stats = load_stats(stats_file)
    stats["total_song_searches"] = stats.get("total_song_searches", 0) + 1
    stats["session_song_searches"] = stats.get("session_song_searches", 0) + 1
    save_stats(stats, stats_file)
    emit_event(EventTopic.STATS_UPDATED)
    return stats


def increment_song_request(stats_file: str = STATS_FILE) -> Dict[str, Any]:
    """Atomically increment both total and session song request counters and emit once."""
    stats = load_stats(stats_file)
    stats["total_song_requests"] = stats.get("total_song_requests", 0) + 1
    stats["session_song_requests"] = stats.get("session_song_requests", 0) + 1
    save_stats(stats, stats_file)
    emit_event(EventTopic.STATS_UPDATED)
    return stats
