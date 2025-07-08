"""
Music-related commands for searching and requesting songs
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

from config.settings import Settings
from utils.traktor import parse_traktor_collection, load_collection_json, search_collection_json
from utils.helpers import check_channel_permissions, truncate_response
from utils.logger import debug, info, warning, error
from utils.stats import increment_stat
from utils.events import emit


class MusicCog(commands.Cog, name="Music"):
    """Cog for music search and song request functionality"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_song_waits = {}  # user_id: asyncio.Task
    
    @app_commands.command(name="song", description="Search for a song in the Traktor collection and optionally select one by replying.")
    @app_commands.describe(search="search query")
    async def song(self, interaction: discord.Interaction, search: str):
        """Search for songs in the Traktor collection with interactive selection"""
        if not check_channel_permissions(interaction, Settings.CHANNEL_IDS):
            await interaction.response.send_message(
                "This command can only be used in the designated channels.", 
                ephemeral=True
            )
            return        # Load collection JSON for fast searching
        songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
        # Increment search counter for GUI tracking
        increment_stat("total_song_searches", 1)
        increment_stat("session_song_searches", 1)

        if not songs:
            await interaction.response.send_message("Collection not available. Please refresh the collection.", ephemeral=True)
            warning(f"Collection JSON not found or empty for {interaction.user}'s search")
            return        # Fast JSON-based search (get all matches, we'll fit what we can in Discord's limit)
        results, total_matches = search_collection_json(songs, search)  # No artificial limit

        if not results:
            await interaction.response.send_message("No matching results found.")
            info(f"{interaction.user}'s search '{search}' matched 0 songs")
            return
              # Dynamically fit as many results as possible within Discord's 2000 character limit
        base_message = "Search Results:\n"
        instruction_message = "\nTo request a song, immediately REPLY with the # of the song, e.g. 6."        # Calculate message endings dynamically
        no_truncation_ending = f"\n� Showing {len(results)} results.{instruction_message}"
        
        # Format: "\n🎶 Showing XXX of YYY results.\nTo request a song..." (when truncation needed)  
        truncation_ending_template = f"\n🎶 Showing {{}} of {total_matches} results.{instruction_message}"
        
        # Calculate available space - try without truncation first
        available_space_no_truncation = 2000 - len(base_message) - len(no_truncation_ending) - 2  # 2 char buffer
        
        # Fit as many results as possible
        fitted_results = []
        current_length = 0
        
        for result in results:
            result_line = result + "\n"
            if current_length + len(result_line) > available_space_no_truncation:
                break
            fitted_results.append(result)
            current_length += len(result_line)
        
        # Build the message
        results_text = "\n".join(fitted_results)
        
        # Check if we need truncation
        if len(fitted_results) < total_matches:
            # We need truncation - recalculate with truncation ending
            truncation_ending = truncation_ending_template.format(len(fitted_results))
            
            # Recalculate available space with truncation ending
            available_space_truncation = 2000 - len(base_message) - len(truncation_ending) - 2  # 2 char buffer
            
            # Re-fit results with truncation space
            fitted_results = []
            current_length = 0
            
            for result in results:
                result_line = result + "\n"
                if current_length + len(result_line) > available_space_truncation:
                    break
                fitted_results.append(result)
                current_length += len(result_line)
              # Rebuild results text and final message
            results_text = "\n".join(fitted_results)
            truncation_ending = truncation_ending_template.format(len(fitted_results))  # Update count
            results_message = base_message + results_text + truncation_ending
        else:
            # No truncation needed
            no_truncation_ending = f"\n🎶 Showing {len(fitted_results)} results.{instruction_message}"
            results_message = base_message + results_text + no_truncation_ending
        
        debug(f"Message length: {len(results_message)}/2000 characters")
        debug(f"Showing {len(fitted_results)} results out of {total_matches} total matches")
        
        await interaction.response.send_message(results_message)
        info(f"{interaction.user}'s search '{search}' matched {total_matches} songs")
        
        # Store only the fitted results in the result_dict
        result_dict = {str(i + 1): result.split(" | ", 1)[1] for i, result in enumerate(fitted_results)}

        user_id = interaction.user.id

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content in result_dict.keys()

        # Cancel any previous wait for this user
        if user_id in self.active_song_waits:
            self.active_song_waits[user_id].cancel()

        async def wait_for_selection():
            try:
                msg = await self.bot.wait_for("message", timeout=Settings.TIMEOUT, check=check)
                selected_song = result_dict[msg.content]            # Save the selected song request to a JSON file
                song_requests_file = Settings.SONG_REQUESTS_FILE
                if song_requests_file:
                    try:
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(song_requests_file), exist_ok=True)
                        
                        # Load existing requests or initialize an empty list
                        if os.path.exists(song_requests_file):
                            with open(song_requests_file, "r", encoding="utf-8") as file:
                                try:
                                    song_requests = json.load(file)
                                except json.JSONDecodeError:
                                    song_requests = []  # Start fresh if JSON is invalid
                                    warning(f"⚠️ Invalid JSON in {song_requests_file}, starting with empty list")
                        else:
                            song_requests = []
                            info(f"📄 Creating new song requests file: {song_requests_file}")

                        # Determine the next request number
                        next_request_num = len(song_requests) + 1

                        # Get the current system date and time
                        current_time = datetime.now().strftime("%Y-%m-%d")

                        # Construct request object
                        new_request = {
                            "RequestNumber": next_request_num,
                            "Date": current_time,
                            "User": str(interaction.user),
                            "Song": selected_song
                        }                    # Append the new request to the list
                        song_requests.append(new_request)
                        
                        # Save back to the JSON file
                        with open(song_requests_file, "w", encoding="utf-8") as file:
                            json.dump(song_requests, file, indent=4)

                        info(f"{interaction.user} selected and requested the song: {selected_song}")
                        await interaction.followup.send(f"Added the song to the Song Request List: {selected_song}")
                        emit("song_request_added", new_request)  # Emit event for new song request
                        # Increment search counter for GUI tracking
                        increment_stat("total_song_requests", 1)
                        increment_stat("session_song_requests", 1)

                        
                    except Exception as e:
                        error(f"❌ Error saving song request: {e}")
                        await interaction.followup.send("❌ Error saving song request. Please try again.", ephemeral=True)
                    
            except asyncio.TimeoutError:
                warning(f"{interaction.user} did not respond in time for song selection.")
            except asyncio.CancelledError:
                # Optionally notify user their previous selection was cancelled
                pass
            except KeyError:
                await interaction.followup.send("Invalid input for song selection.")
                warning(f"{interaction.user} entered invalid input for song selection.")
            finally:
                if user_id in self.active_song_waits:
                    del self.active_song_waits[user_id]

        self.active_song_waits[user_id] = asyncio.create_task(wait_for_selection())
        

async def setup(bot: commands.Bot):
    """Add the MusicCog to the bot"""
    await bot.add_cog(MusicCog(bot))
