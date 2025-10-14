"""
Permission and utility helper functions
"""
from typing import Any, Dict, List
import os
import json
import time
import errno
import discord
from utils.stats import (
    STATS_FILE, load_stats, save_stats, increment_stat, reset_session_stats, reset_global_stats
)

def wrap_text(text: str, max_length: int, *, ellipsis: str = "…") -> str:
    """Return *text* trimmed to *max_length* characters (including ellipsis)."""

    if max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    cutoff = max_length - len(ellipsis)
    if cutoff <= 0:
        return ellipsis[:max_length]
    return text[:cutoff] + ellipsis

def check_permissions(user_id: int, allowed_user_ids: List[int]) -> bool:
    """Check if a user has permission based on their ID"""
    return user_id in allowed_user_ids


def check_channel_permissions(interaction: discord.Interaction, channel_ids: List[int]) -> bool:
    """Check if the command is being used in an allowed channel"""
    if not interaction.channel or not channel_ids:
        return False
    return interaction.channel.id in channel_ids


def format_song_requests(song_requests: List[dict]) -> str:
    """Format song requests for display.

    Prefers new structured fields (Artist/Title) when present, falls back to legacy 'Song'.
    Includes optional Time when available.
    """
    if not song_requests:
        return "No song requests found."

    formatted_requests = []
    for entry in song_requests:
        rn = entry.get("RequestNumber", "?")
        date = entry.get("Date", "")
        time = entry.get("Time", "")
        user = entry.get("User", "")
        artist = entry.get("Artist")
        title = entry.get("Title")
        if artist or title:
            song_str = f"{artist or ''} | {title or ''}".strip(" |")
        else:
            song_str = entry.get("Song", "")
        dt_part = f"{date} {time}".strip()
        formatted_requests.append(f"{rn} | {dt_part} | {user} | {song_str}")
    response = "\n".join(formatted_requests)
    
    # Ensure the message length doesn't exceed Discord's limit
    if len(response) > 2000:
        response = response[:1958] + "..." + "\nDisplaying oldest requested songs only"
    
    return response


def truncate_response(response: str, max_length: int = 2000) -> str:
    """Truncate response to fit Discord's message limits"""
    if len(response) > max_length:
        return response[:max_length - 3] + "..."
    return response


def update_request_numbers(song_requests):
    """Update the request numbers in the song requests list"""
    for i, req in enumerate(song_requests):
        req["RequestNumber"] = i + 1


def safe_write_json(
    path: str,
    data: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    retries: int = 3,
    backoff: float = 0.1,
) -> None:
    """Atomically write JSON to disk with optional retry on common Windows locks.

    Strategy:
    - Write to a temporary file in the same directory
    - fsync to ensure bytes hit disk
    - Replace the target (atomic on the same filesystem)
    - Retry a few times on PermissionError/EBUSY/EPERM/EACCES
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"

    def _attempt_write() -> None:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)

    attempt = 0
    last_err: Exception | None = None
    while attempt < max(1, retries):
        try:
            _attempt_write()
            return
        except OSError as e:
            last_err = e
            if isinstance(e, PermissionError) or e.errno in {errno.EBUSY, errno.EPERM, errno.EACCES}:
                time.sleep(backoff * (2 ** attempt))
                attempt += 1
                continue
            raise
        except Exception as e:
            last_err = e
            # Non-OS errors generally won't benefit from retry
            break
    if last_err:
        raise last_err
