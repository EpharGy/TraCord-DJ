"""
Admin commands for DJ operations and bot management
"""
import discord
from discord.ext import commands
from discord import app_commands
import json
import shutil
import os
from typing import List

from config.settings import Settings
from utils.helpers import check_permissions


class AdminCog(commands.Cog, name="Admin"):
    """Cog for administrative commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="srbnpclear", description="Backup and clear track history in NowPlaying config.json")
    async def srbnpclear(self, interaction: discord.Interaction):
        """Backup and clear NowPlaying track history (admin only)"""
        if not Settings.NOWPLAYING_CONFIG_JSON_PATH:
            await interaction.response.send_message(
                "Config file path not set in environment variable NOWPLAYING_CONFIG_JSON_PATH.", 
                ephemeral=True
            )
            return

        if not check_permissions(interaction.user.id, Settings.ALLOWED_USER_IDS):
            await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
            return

        try:
            # Backup config.json
            backup_path = Settings.NOWPLAYING_CONFIG_JSON_PATH + ".bak"
            shutil.copyfile(Settings.NOWPLAYING_CONFIG_JSON_PATH, backup_path)

            # Load config.json
            with open(Settings.NOWPLAYING_CONFIG_JSON_PATH, "r", encoding="utf-8") as file:
                config = json.load(file)

            # Clear specific fields in currentTrack
            fields_to_clear = ["title", "artist", "comment", "label", "album", "artwork"]
            if "currentTrack" in config:
                for field in fields_to_clear:
                    if field in config["currentTrack"]:
                        config["currentTrack"][field] = ""

            # Clear track list
            if "trackList" in config:
                config["trackList"] = []

            # Save updated config.json
            with open(Settings.NOWPLAYING_CONFIG_JSON_PATH, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4)

            await interaction.response.send_message(
                f"NowPlaying config cleared successfully. Backup saved as {backup_path}"
            )
            print(f"{interaction.user} cleared NowPlaying config")

        except Exception as e:
            print(f"Error clearing NowPlaying config: {e}")
            await interaction.response.send_message(f"Error clearing NowPlaying config: {e}", ephemeral=True)
    
    @app_commands.command(name="srblive", description="Sends a live notification message with optional role mentions")
    @app_commands.describe(message="The message to send with the notification")
    async def srblive(self, interaction: discord.Interaction, message: str):
        """Send live streaming notifications with role mentions (admin only)"""
        if not check_permissions(interaction.user.id, Settings.ALLOWED_USER_IDS):
            await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
            return

        # If no roles are configured, send a simple notification
        if not Settings.DISCORD_LIVE_NOTIFICATION_ROLES:
            await interaction.response.send_message(f"🔴 **LIVE NOW** 🔴\n{message}")
            print(f"{interaction.user} sent live notification (no roles configured): {message}")
            return
        
        # Get all configured roles from the guild
        role_mentions = []
        missing_roles = []
        
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        for role_name in Settings.DISCORD_LIVE_NOTIFICATION_ROLES:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                role_mentions.append(role.mention)
            else:
                missing_roles.append(role_name)
        
        # Create the notification message
        if role_mentions:
            role_ping = " ".join(role_mentions)
            notification_message = f"🔴 **LIVE NOW** 🔴\n{message}\n\n{role_ping}"
        else:
            notification_message = f"🔴 **LIVE NOW** 🔴\n{message}"
        
        # Send the notification
        await interaction.response.send_message(notification_message)
        
        # Log the action and any missing roles
        if missing_roles:
            print(f"{interaction.user} sent live notification with missing roles: {missing_roles}")
        else:
            print(f"{interaction.user} sent live notification: {message}")


async def setup(bot: commands.Bot):
    """Add the AdminCog to the bot"""
    await bot.add_cog(AdminCog(bot))
