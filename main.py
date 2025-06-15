"""
DJ Discord Bot - Main Entry Point
A comprehensive Discord bot for managing music requests, interacting with Traktor DJ software collections,
and enhancing DJ workflow automation.

This bot uses Discord.py Cogs for modular organization.
"""
import asyncio
import os
import shutil
import discord
from discord.ext import commands

# Import configuration
from config.settings import Settings
from utils.traktor import count_songs_in_collection, get_new_songs


class DJBot(commands.Bot):
    """Custom bot class with setup methods"""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message-based interactions
        
        super().__init__(
            command_prefix='!',  # Keep for compatibility, mainly using slash commands
            intents=intents,
            application_id=Settings.APPLICATION_ID
        )
    
    async def setup_hook(self):
        """Load all cogs when the bot starts"""
        print("Loading cogs...")
        
        # List of cogs to load
        cogs = [
            'cogs.music',
            'cogs.collection', 
            'cogs.requests',
            'cogs.admin'
        ]
        
        # Load each cog
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Event fired when bot is ready"""
        print('━' * 50)
        print(f'🎵 DJ Discord Bot Loaded')
        print(f'🤖 Logged in as {self.user} (ID: {self.user.id if self.user else "Unknown"})')
        print(f'🗄️ Using Cogs architecture')
        print('━' * 50)
        
        # Initialize collection file
        await self._initialize_collection()
        
        print('✅ Bot is ready and operational!')
        print('━' * 50)
    
    async def _initialize_collection(self):
        """Copy Traktor collection file and display statistics"""
        try:
            copied_file_path = os.path.join(os.getcwd(), "collection.nml")
            shutil.copyfile(Settings.TRAKTOR_PATH, copied_file_path)
            print("📁 Traktor collection file copied successfully")
            
            # Count the number of songs in the collection and print statistics
            total_songs = count_songs_in_collection(copied_file_path, Settings.EXCLUDED_ITEMS)
            _, total_new_songs = get_new_songs(
                copied_file_path, Settings.NEW_SONGS_DAYS, 
                Settings.EXCLUDED_ITEMS, Settings.MAX_SONGS, Settings.DEBUG
            )
            
            print(f"📊 Statistics:")
            print(f"   • Max songs returned per search: {Settings.MAX_SONGS}")
            print(f"   • Default days for new songs: {Settings.NEW_SONGS_DAYS}")
            print(f"   • Total songs in collection: {total_songs:,}")
            print(f"   • New songs (last {Settings.NEW_SONGS_DAYS} days): {total_new_songs}")
            
        except Exception as e:
            print(f"❌ Error initializing collection: {e}")


async def main():
    """Main function to start the bot"""
    if not Settings.TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please check your .env file and ensure DISCORD_TOKEN is set.")
        return
    
    print("🚀 Starting DJ Discord Bot...")
    
    # Create and start the bot
    bot = DJBot()
    
    try:
        async with bot:
            await bot.start(Settings.TOKEN)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot encountered an error: {e}")
    finally:
        print("👋 Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
