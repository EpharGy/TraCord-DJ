"""
Permission and utility helper functions
"""
from typing import List
import discord
from utils.logger import info, warning
from utils.stats import (
    STATS_FILE, load_stats, save_stats, increment_stat, reset_session_stats, reset_global_stats
)


def check_permissions(user_id: int, allowed_user_ids: List[int]) -> bool:
    """Check if a user has permission based on their ID"""
    return user_id in allowed_user_ids


def check_channel_permissions(interaction: discord.Interaction, channel_ids: List[int]) -> bool:
    """Check if the command is being used in an allowed channel"""
    if not interaction.channel or not channel_ids:
        return False
    return interaction.channel.id in channel_ids


def format_song_requests(song_requests: List[dict]) -> str:
    """Format song requests for display"""
    if not song_requests:
        return "No song requests found."
    
    formatted_requests = [
        f"{entry['RequestNumber']} | {entry['Date']} | {entry['User']} | {entry['Song']}" 
        for entry in song_requests
    ]
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
