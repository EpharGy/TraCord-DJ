"""
TraCord DJ - Main Entry Point

Comprehensive Discord bot for managing music requests, interacting with Traktor DJ software collections,
and enhancing DJ workflow automation.

This bot uses Discord.py Cogs for modular organization.
"""
import asyncio
import os
import shutil
import logging

import discord
from discord.ext import commands

from tracord.infra.logging import setup_for_environment

# Import configuration and utilities
from config.settings import Settings
from utils.traktor import refresh_collection_json, load_collection_json, count_songs_in_collection_json, get_new_songs_json
from utils.logger import get_logger

setup_for_environment()

logger = get_logger(__name__)


class DJBot(commands.Bot):
    """Custom bot class with setup methods"""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message-based interactions
        
        super().__init__(
            command_prefix='!',  # Keep for compatibility, mainly using slash commands
            intents=intents,
            application_id=Settings.get('DISCORD_BOT_APP_ID')
        )
    
    async def setup_hook(self):
        """Load internal cogs (always), then dynamically load external cogs if present."""
        import os
        import importlib
        # Load internal cogs from _internal_cogs.py
        try:
            from cogs._internal_cogs import INTERNAL_COGS
            loaded_cogs = set()
            for cog in INTERNAL_COGS:
                try:
                    await self.load_extension(cog)
                    logger.info(f"✅ Loaded internal {cog}")
                    loaded_cogs.add(cog)
                except Exception as e:
                    if cog.startswith("extra_cogs."):
                        # Suppress error for missing extra_cogs cogs
                        pass
                    else:
                        logger.error(f"❌ Failed to load internal {cog}: {e}")
        except Exception as e:
            logger.warning(f"Could not import internal cogs list: {e}")
            loaded_cogs = set()
        # Dynamically load external cogs (skip any already loaded)
        cogs_dir = "cogs"
        if os.path.isdir(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("_") and filename != "__init__.py":
                    cog = f"cogs.{filename[:-3]}"
                    if cog not in loaded_cogs:
                        try:
                            await self.load_extension(cog)
                            logger.info(f"✅ Loaded external {cog}")
                        except Exception as e:
                            logger.error(f"❌ Failed to load external {cog}: {e}")
        else:
            logger.info("No external cogs directory found. Skipping extra cogs loading.")
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands")
            logger.info("✅ Waiting for Bot initialization...")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")
        
    async def on_ready(self):
        """Event fired when bot is ready"""
        logger.info('━' * 50)
        logger.info('🎵 TraCord DJ Loaded')
        logger.info(f'🤖 Logged in as {self.user} (ID: {self.user.id if self.user else "Unknown"})')
        logger.info('🗄️ Using Cogs architecture')
        logger.info('━' * 50)

        # Initialize collection file
        await self._initialize_collection()

        logger.info('✅ Bot is ready and operational!')
        logger.info('━' * 50)

    async def _initialize_collection(self):
        """Initialize collection by converting XML to JSON and display statistics"""
        try:
            logger.info("🔄 Initializing collection system...")
            # Use the new JSON refresh workflow
            song_count = refresh_collection_json(
                Settings.TRAKTOR_PATH, 
                Settings.COLLECTION_JSON_FILE, 
                Settings.EXCLUDED_ITEMS, 
                debug_mode=Settings.DEBUG
            )
            
            logger.info(f"✅ Collection imported successfully - {song_count:,} songs processed")
            # Load the JSON collection for statistics
            songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
            if songs:
                total_songs = count_songs_in_collection_json(songs)
                _, total_new_songs = get_new_songs_json(songs, Settings.NEW_SONGS_DAYS, Settings.MAX_SONGS, Settings.DEBUG)
                
                logger.info(
                    f"📊 Collection stats: {total_songs:,} total songs, {total_new_songs:,} new songs (last {Settings.NEW_SONGS_DAYS} days)"
                )
                logger.debug(f"   • Max songs returned per search: {Settings.MAX_SONGS}")
                logger.debug(f"   • Default days for new songs: {Settings.NEW_SONGS_DAYS}")
            else:
                logger.warning("⚠️ Collection JSON is empty or could not be loaded")
            
        except Exception as e:
            logger.error(f"❌ Error initializing collection: {e}")


async def main():
    """Main function to start the bot"""
    if not Settings.get('DISCORD_TOKEN'):
        logger.error("❌ ERROR: DISCORD_TOKEN not found in settings.json!")
        logger.error("Please check your settings.json file and ensure DISCORD_TOKEN is set.")
        return

    logger.info("🚀 Starting TraCord DJ...")
    
    # Create and start the bot
    bot = DJBot()
    
    try:
        async with bot:
            await bot.start(str(Settings.get('DISCORD_TOKEN') or ''))
    except KeyboardInterrupt:
        logger.warning("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot encountered an error: {e}")
    finally:
        logger.info("👋 Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
