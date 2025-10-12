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
from typing import Dict, List, Tuple

from config.settings import Settings
from utils.helpers import check_channel_permissions, wrap_text
from utils.logger import get_logger
from utils.stats import increment_stat
from utils.events import emit
from tracord.core.services.search import JsonSearchBackend


logger = get_logger(__name__)


class MusicCog(commands.Cog, name="Music"):
    """Cog for music search and song request functionality."""

    MAX_MESSAGE_LENGTH = 2000

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_song_waits: Dict[int, asyncio.Task] = {}
        self.search_backend = JsonSearchBackend.from_settings(Settings)
    
    @app_commands.command(name="song", description="Search for a song in the Traktor collection and optionally select one by replying.")
    @app_commands.describe(search="search query")
    async def song(self, interaction: discord.Interaction, search: str):
        """Search for songs in the Traktor collection with interactive selection"""
        if not self._is_channel_allowed(interaction):
            await interaction.response.send_message(
                "This command can only be used in the designated channels.",
                ephemeral=True,
            )
            return

        if not await self._ensure_collection_loaded(interaction):
            return

        self._record_search()

        search_result = self.search_backend.search(search)
        matches = search_result.matches or []
        total_matches = search_result.total_matches

        if not matches:
            await interaction.response.send_message("No matching results found.")
            logger.info(f"{interaction.user}'s search '{search}' matched 0 songs")
            return

        message, displayed_results = self._build_search_response(matches, total_matches)
        await interaction.response.send_message(message)
        logger.info(f"{interaction.user}'s search '{search}' matched {total_matches} songs")

        result_dict: Dict[str, str] = {}
        for index, original in enumerate(displayed_results, start=1):
            _, _, detail = original.partition(" | ")
            result_dict[str(index)] = detail or original

        user_id = interaction.user.id

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content in result_dict.keys()

        # Cancel any previous wait for this user
        if user_id in self.active_song_waits:
            self.active_song_waits[user_id].cancel()

        async def wait_for_selection():
            try:
                msg = await self.bot.wait_for("message", timeout=Settings.TIMEOUT, check=check)
                selected_song = result_dict[msg.content]
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
                                    logger.warning(
                                        f"⚠️ Invalid JSON in {song_requests_file}, starting with empty list"
                                    )
                        else:
                            song_requests = []
                            logger.info(f"📄 Creating new song requests file: {song_requests_file}")

                        # Determine the next request number
                        next_request_num = len(song_requests) + 1

                        # Get the current system date and time
                        current_time = datetime.now().strftime("%Y-%m-%d")

                        # Construct request object
                        new_request = {
                            "RequestNumber": next_request_num,
                            "Date": current_time,
                            "User": str(interaction.user),
                            "Song": selected_song,
                        }

                        # Append the new request to the list
                        song_requests.append(new_request)

                        # Save back to the JSON file
                        with open(song_requests_file, "w", encoding="utf-8") as file:
                            json.dump(song_requests, file, indent=4)

                        logger.info(
                            f"{interaction.user} selected and requested the song: {selected_song}"
                        )
                        await interaction.followup.send(
                            f"Added the song to the Song Request List: {selected_song}"
                        )
                        emit("song_request_added", new_request)  # Emit event for new song request
                        # Increment search counter for GUI tracking
                        increment_stat("total_song_requests", 1)
                        increment_stat("session_song_requests", 1)

                    except Exception as exc:
                        logger.error(f"❌ Error saving song request: {exc}")
                        await interaction.followup.send(
                            "❌ Error saving song request. Please try again.", ephemeral=True
                        )
                    
            except asyncio.TimeoutError:
                logger.warning(f"{interaction.user} did not respond in time for song selection.")
            except asyncio.CancelledError:
                # Optionally notify user their previous selection was cancelled
                pass
            except KeyError:
                await interaction.followup.send("Invalid input for song selection.")
                logger.warning(f"{interaction.user} entered invalid input for song selection.")
            finally:
                if user_id in self.active_song_waits:
                    del self.active_song_waits[user_id]

        self.active_song_waits[user_id] = asyncio.create_task(wait_for_selection())
        
    def _is_channel_allowed(self, interaction: discord.Interaction) -> bool:
        return check_channel_permissions(interaction, Settings.CHANNEL_IDS)

    async def _ensure_collection_loaded(self, interaction: discord.Interaction) -> bool:
        if self.search_backend.song_count() == 0:
            self.search_backend.reload()
        if self.search_backend.song_count() > 0:
            return True

        message = "Collection not available. Please refresh the collection."
        logger.warning(f"Collection JSON not found or empty for {interaction.user}'s search")
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return False

    def _record_search(self) -> None:
        increment_stat("total_song_searches", 1)
        increment_stat("session_song_searches", 1)

    def _footer_text(self, shown: int, total: int) -> str:
        total_display = max(total, shown)
        return (
            f"\n🎶 Showing {shown} of {total_display} results."
            "\nTo request a song, reply with the # (e.g. 6)."
        )

    def _build_search_response(self, matches: List[str], total_matches: int) -> Tuple[str, List[str]]:
        base = "Search Results:\n"
        display_lines: List[str] = []
        originals: List[str] = []

        for original in matches:
            candidate_lines = display_lines + [original]
            candidate_body = "\n".join(candidate_lines)
            candidate_footer = self._footer_text(len(candidate_lines), total_matches)
            candidate_message = base + candidate_body + candidate_footer

            if len(candidate_message) <= self.MAX_MESSAGE_LENGTH:
                display_lines.append(original)
                originals.append(original)
                continue

            if not display_lines:
                footer = self._footer_text(1, total_matches)
                available = self.MAX_MESSAGE_LENGTH - len(base) - len(footer)
                trimmed = wrap_text(original, max(0, available))
                display_lines.append(trimmed)
                originals.append(original)
            break

        if not display_lines and matches:
            footer = self._footer_text(1, total_matches)
            available = self.MAX_MESSAGE_LENGTH - len(base) - len(footer)
            trimmed = wrap_text(matches[0], max(0, available))
            display_lines.append(trimmed)
            originals.append(matches[0])

        shown = len(display_lines)
        footer = self._footer_text(shown, total_matches)
        message_body = "\n".join(display_lines)
        message = base + message_body + footer
        logger.debug(
            f"[MusicCog] song results message length: {len(message)}/{self.MAX_MESSAGE_LENGTH}; "
            f"showing {shown} of {total_matches}"
        )
        return message, originals


async def setup(bot: commands.Bot):
    """Add the MusicCog to the bot"""
    await bot.add_cog(MusicCog(bot))
