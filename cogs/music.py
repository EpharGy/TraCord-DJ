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
from utils.traktor import parse_traktor_collection
from utils.helpers import check_channel_permissions, truncate_response


class MusicCog(commands.Cog, name="Music"):
    """Cog for music search and song request functionality"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def _increment_search_counter(self):
        """Increment the search counter in a file for GUI tracking"""
        try:
            search_counter_file = Settings.SEARCH_COUNTER_FILE
            try:
                with open(search_counter_file, "r") as f:
                    count = int(f.read().strip())
            except (FileNotFoundError, ValueError):
                count = 0
            
            count += 1
            with open(search_counter_file, "w") as f:
                f.write(str(count))
        except Exception as e:
            print(f"Error updating search counter: {e}")
    
    @app_commands.command(name="song", description="Search for a song in the Traktor collection and optionally select one by replying.")
    @app_commands.describe(search="search query")
    async def song(self, interaction: discord.Interaction, search: str):
        """Search for songs in the Traktor collection with interactive selection"""
        if not check_channel_permissions(interaction, Settings.CHANNEL_IDS):
            await interaction.response.send_message(
                "This command can only be used in the designated channels.", 
                ephemeral=True
            )
            return

        copied_file_path = os.path.join(os.getcwd(), "collection.nml")
        results, total_matches = parse_traktor_collection(
            copied_file_path, search, Settings.EXCLUDED_ITEMS, 
            Settings.MAX_SONGS, Settings.DEBUG
        )

        if not results:
            await interaction.response.send_message("No matching results found.")
            print(f"{interaction.user}'s search '{search}' matched 0 songs")
            return

        # Limit the results to MAX_SONGS for display
        displayed_results = results[:Settings.MAX_SONGS]
        instruction_message = "\n\nTo request a song, immediately REPLY with the # of the song, e.g. 6."
        
        results_message = "Search Results:\n" + "\n".join(displayed_results) + instruction_message

        # Add a note if there are more matches than MAX_SONGS
        if len(results) > Settings.MAX_SONGS:
            results_message += f"\n\n**{Settings.MAX_SONGS} of {total_matches} matches displayed. Refine your search if needed.**"
        
        await interaction.response.send_message(results_message)
        print(f"{interaction.user}'s search '{search}' matched {total_matches} songs")
        
        # Increment search counter for GUI tracking
        self._increment_search_counter()

        # Store only the displayed results in the result_dict
        result_dict = {str(i + 1): result.split(" | ", 1)[1] for i, result in enumerate(displayed_results)}

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content in result_dict.keys()

        try:
            # Wait for user input with a timeout
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
                                print(f"⚠️ Invalid JSON in {song_requests_file}, starting with empty list")
                    else:
                        song_requests = []
                        print(f"📄 Creating new song requests file: {song_requests_file}")

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

                    print(f"{interaction.user} selected and saved the song: {selected_song}")
                    await interaction.followup.send(f"Added the song to the Song Request List: {selected_song}")
                    
                except Exception as e:
                    print(f"❌ Error saving song request: {e}")
                    await interaction.followup.send("❌ Error saving song request. Please try again.", ephemeral=True)
                    
        except asyncio.TimeoutError:
            print(f"{interaction.user} did not respond in time for song selection.")
        except KeyError:
            await interaction.followup.send("Invalid input for song selection.")
            print(f"{interaction.user} entered invalid input for song selection.")


async def setup(bot: commands.Bot):
    """Add the MusicCog to the bot"""
    await bot.add_cog(MusicCog(bot))
