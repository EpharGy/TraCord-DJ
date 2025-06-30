"""
Song request management commands
"""
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from typing import List, Dict, Any

from config.settings import Settings
from utils.helpers import check_permissions, format_song_requests
from utils.logger import debug, info, warning, error
from utils.events import emit


class RequestsCog(commands.Cog, name="Requests"):
    """Cog for song request list management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def _load_song_requests(self) -> List[Dict[str, Any]]:
        """Load song requests from JSON file"""
        if not Settings.SONG_REQUESTS_FILE or not os.path.exists(Settings.SONG_REQUESTS_FILE):
            return []
        
        try:
            with open(Settings.SONG_REQUESTS_FILE, "r", encoding="utf-8") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return []  # Fallback if the file has invalid JSON
        except Exception:
            return []
    
    def _save_song_requests(self, song_requests: List[Dict[str, Any]]) -> None:
        """Save song requests to JSON file"""
        try:
            with open(Settings.SONG_REQUESTS_FILE, "w", encoding="utf-8") as file:
                json.dump(song_requests, file, indent=4)
        except Exception as e:
            error(f"Error saving song requests: {e}")
    
    def _update_request_numbers(self, song_requests: List[Dict[str, Any]]) -> None:
        """Update request numbers to be sequential"""
        for i, req in enumerate(song_requests):
            req["RequestNumber"] = i + 1
    
    @app_commands.command(name="srbreqlist", description="Display all songs currently in the song request list")
    async def srbreqlist(self, interaction: discord.Interaction):
        """Display all pending song requests"""
        song_requests = self._load_song_requests()
        
        if not song_requests:
            await interaction.response.send_message("No song requests found.")
            info(f"{interaction.user} viewed the song request list.")
            return
        
        response = format_song_requests(song_requests)
        await interaction.response.send_message(response)
        info(f"{interaction.user} viewed the song request list.")
    
    @app_commands.command(name="srbreqdel", description="Delete a song request by RequestNumber, 'all', 'self', or a specific user")
    @app_commands.describe(request_number="RequestNumber to delete, 'all', 'self', or a specific user")
    async def srbreqdel(self, interaction: discord.Interaction, request_number: str):
        """Delete song requests with various options"""
        song_requests = self._load_song_requests()
        
        if not song_requests:
            await interaction.response.send_message("Song Request List is empty.")
            return

        try:
            # Handle 'all' deletion
            if request_number.lower() == "all":
                # Check if the user has permission to delete all
                if not check_permissions(interaction.user.id, Settings.ADMIN_IDS):
                    await interaction.response.send_message(
                        "You do not have permission to delete all song requests.", 
                        ephemeral=True
                    )
                    return

                # Clear all requests
                song_requests = []
                self._save_song_requests(song_requests)
                emit("song_request_deleted", None)  # Emit event for any deletion

                await interaction.response.send_message("All song requests have been deleted.")
                info(f"{interaction.user} deleted all song requests.")
                return

            # Handle 'self' deletion
            if request_number.lower() == "self":
                # Remove all requests where the requesting user is the "User" of the JSON entry
                user_requests = [req for req in song_requests if req["User"] == str(interaction.user)]
                if not user_requests:
                    await interaction.response.send_message("You have no song requests to delete.")
                    return

                # Filter out the user's requests
                song_requests = [req for req in song_requests if req["User"] != str(interaction.user)]

                # Update RequestNumbers
                self._update_request_numbers(song_requests)
                self._save_song_requests(song_requests)
                emit("song_request_deleted", None)  # Emit event for any deletion

                # Format the updated song list
                updated_list = format_song_requests(song_requests)

                await interaction.response.send_message("All your song requests have been deleted.\nUpdated Song Request List:")
                info(f"{interaction.user} deleted all their song requests.")
                await interaction.followup.send(updated_list)
                return

            # Check if the input is numeric (for individual song deletion)
            if request_number.isdigit():
                request_num = int(request_number)

                # Validate the request_number
                if request_num < 1 or request_num > len(song_requests):
                    await interaction.response.send_message("RequestNumber not found.")
                    return

                request_to_delete = song_requests[request_num - 1]

                # Check if the user has permission to delete the specific request
                if (not check_permissions(interaction.user.id, Settings.ADMIN_IDS) and 
                    str(interaction.user) != request_to_delete["User"]):
                    await interaction.response.send_message(
                        "You do not have permission to delete this song request.", 
                        ephemeral=True
                    )
                    return

                # Remove the request and update RequestNumbers
                song_requests.pop(request_num - 1)
                self._update_request_numbers(song_requests)
                self._save_song_requests(song_requests)
                emit("song_request_deleted", None)  # Emit event for any deletion

                # Format the deleted song details
                deleted_song_details = f"#{request_number} | {request_to_delete['Date']} | {request_to_delete['User']} | {request_to_delete['Song']} has been deleted."

                # Format the updated song list
                updated_list = format_song_requests(song_requests)

                # Send the response
                await interaction.response.send_message(f"Deleting Song Request\n({deleted_song_details})\nUpdated Song Request List:")
                info(f"{interaction.user} deleted song request #{request_number}.")
                await interaction.followup.send(updated_list)
                return

            # Handle specific user deletion
            target_user = request_number
            if target_user:
                # Check if the requesting user has permission to delete another user's requests
                if (not check_permissions(interaction.user.id, Settings.ADMIN_IDS) and 
                    str(interaction.user) != target_user):
                    await interaction.response.send_message(
                        "You do not have permission to delete all requests from this user.", 
                        ephemeral=True
                    )
                    return

                # Find all requests by the target user
                user_requests = [req for req in song_requests if req["User"] == target_user]
                if not user_requests:
                    await interaction.response.send_message(f"No song requests found for user '{target_user}'.")
                    return

                # Filter out the target user's requests
                song_requests = [req for req in song_requests if req["User"] != target_user]

                # Update RequestNumbers
                self._update_request_numbers(song_requests)
                self._save_song_requests(song_requests)
                emit("song_request_deleted", None)  # Emit event for any deletion

                # Format the updated song list
                updated_list = format_song_requests(song_requests)

                await interaction.response.send_message(f"All song requests from user '{target_user}' have been deleted.\nUpdated Song Request List:")
                info(f"{interaction.user} deleted all song requests from user '{target_user}'.")
                await interaction.followup.send(updated_list)
                return

        except Exception as e:
            error(f"Error deleting song request: {e}")
            await interaction.response.send_message(f"Error deleting song request: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    """Add the RequestsCog to the bot"""
    await bot.add_cog(RequestsCog(bot))
