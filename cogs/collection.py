"""
Collection management commands for Traktor integration
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
import shutil

from config.settings import Settings
from utils.traktor import count_songs_in_collection, get_new_songs
from utils.helpers import check_permissions, check_channel_permissions, truncate_response


class CollectionCog(commands.Cog, name="Collection"):
    """Cog for Traktor collection management and new song tracking"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="srbtraktorrefresh", description="Refresh the Traktor collection file")
    async def srbtraktorrefresh(self, interaction: discord.Interaction):
        """Refresh the Traktor collection file (admin only)"""
        if not check_permissions(interaction.user.id, Settings.ALLOWED_USER_IDS):
            await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
            return

        try:
            # Copy the Traktor collection file to the current directory
            copied_file_path = os.path.join(os.getcwd(), "collection.nml")
            shutil.copyfile(Settings.TRAKTOR_PATH, copied_file_path)
            
            # Count the number of songs in the collection
            song_count = count_songs_in_collection(copied_file_path, Settings.EXCLUDED_ITEMS)
            
            # Count the number of new songs
            new_songs, total_new_songs = get_new_songs(
                copied_file_path, Settings.NEW_SONGS_DAYS, 
                Settings.EXCLUDED_ITEMS, Settings.MAX_SONGS, Settings.DEBUG
            )
            
            print(f"{interaction.user} triggered Collection update. Total number of songs: {song_count}")
            print(f"{total_new_songs} songs classed as new (added in the last {Settings.NEW_SONGS_DAYS} days)")
            
            await interaction.response.send_message(
                f"Traktor collection file copied successfully.\n"
                f"Total number of songs in the collection: {song_count}.\n"
                f"Total number of songs added in the last {Settings.NEW_SONGS_DAYS} days: {total_new_songs}"
            )
            
        except Exception as e:
            print(f"{interaction.user} triggered a Collection update, but there was an error copying file")
            await interaction.response.send_message(f"Error copying file: {e}", ephemeral=True)
    
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
        
        copied_file_path = os.path.join(os.getcwd(), "collection.nml")
        results, total_new_songs = get_new_songs(
            copied_file_path, days, Settings.EXCLUDED_ITEMS, 
            Settings.MAX_SONGS, Settings.DEBUG
        )
        
        if Settings.DEBUG:
            print(f"Total new songs found: {total_new_songs}")
            print(f"Results: {results}")
        
        if results:
            response = "\n".join(results)
            # Ensure the message length doesn't exceed Discord's limit
            response = truncate_response(response)
            await interaction.followup.send(response)
            print(f"{interaction.user} requested new songs from the last {days} days, found {total_new_songs} songs")
        else:
            await interaction.followup.send("No new songs found.")
            print(f"{interaction.user} requested new songs from the last {days} days, found 0 songs")


async def setup(bot: commands.Bot):
    """Add the CollectionCog to the bot"""
    await bot.add_cog(CollectionCog(bot))
