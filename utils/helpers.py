"""
Permission and utility helper functions
"""
from typing import List
import discord
from utils.logger import info, warning


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


def load_search_count(search_counter_file: str) -> int:
    """Load the search count from the file, if it exists."""
    try:
        import os
        if os.path.exists(search_counter_file):
            with open(search_counter_file, "r") as f:
                count = f.read().strip()
                search_count = int(count) if count.isdigit() else 0
            info(f"🔍 Loaded search count: {search_count}")
            return search_count
        else:
            info("🔍 Search counter file not found, starting at 0")
            return 0
    except Exception as e:
        warning(f"⚠️ Error loading search count: {e}")
        return 0

def update_search_count_display(search_counter_file: str, current_count: int, update_callback):
    """Update the search count label in the GUI. update_callback should accept the new count."""
    try:
        import os
        if os.path.exists(search_counter_file):
            with open(search_counter_file, "r") as f:
                count = f.read().strip()
                new_count = int(count) if count.isdigit() else 0
                if new_count != current_count:
                    update_callback(new_count)
    except Exception as e:
        warning(f"⚠️ Error updating search count display: {e}")
