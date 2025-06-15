"""
Collection management commands for Traktor integration
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
import shutil

from config.settings import Settings
from utils.traktor import count_songs_in_collection, get_new_songs, load_collection_json, get_new_songs_json, count_songs_in_collection_json
from utils.helpers import check_permissions, check_channel_permissions, truncate_response


class CollectionCog(commands.Cog, name="Collection"):
    """Cog for Traktor collection management and new song tracking"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="srbnew", description=f"Display newly added songs from the last {Settings.NEW_SONGS_DAYS} days")
    @app_commands.describe(days=f"Number of days to look back for new songs (default is {Settings.NEW_SONGS_DAYS} days)")
    async def srbnew(self, interaction: discord.Interaction, days: int = Settings.NEW_SONGS_DAYS):
        """Display newly added songs from the specified number of days"""
        if not check_channel_permissions(interaction, Settings.CHANNEL_IDS):
            await interaction.response.send_message(
                "This command can only be used in the designated channels.", 
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(f"Displaying songs from the last {days} days.")
        
        # Load collection JSON for fast searching
        songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
        if not songs:
            await interaction.followup.send("Collection not available. Please refresh the collection.")
            print(f"Collection JSON not found or empty for {interaction.user}'s new songs request")
            return
            
        results, total_new_songs = get_new_songs_json(songs, days, Settings.MAX_SONGS, Settings.DEBUG)
        
        if Settings.DEBUG:
            print(f"Total new songs found: {total_new_songs}")
            print(f"Results: {results}")
        
        if results:
            # Smart truncation for better user experience
            header = f"Songs from the last {days} days:\n"
            available_space = 2000 - len(header) - 100  # 100 chars buffer
            
            fitted_results = []
            current_length = 0
            
            for result in results:
                result_line = result + "\n"
                if current_length + len(result_line) > available_space:
                    break
                fitted_results.append(result)
                current_length += len(result_line)
            
            response = header + "\n".join(fitted_results)
            
            # Add truncation note if needed
            if len(fitted_results) < len(results):
                response += f"\n... (showing {len(fitted_results)} of {total_new_songs} new songs)"
            
            await interaction.followup.send(response)
            print(f"{interaction.user} requested new songs from the last {days} days, found {total_new_songs} songs")
        else:
            await interaction.followup.send("No new songs found.")
            print(f"{interaction.user} requested new songs from the last {days} days, found 0 songs")


async def setup(bot: commands.Bot):
    """Add the CollectionCog to the bot"""
    await bot.add_cog(CollectionCog(bot))
