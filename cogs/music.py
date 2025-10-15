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
from utils.stats import increment_song_search, increment_song_request
from tracord.core.events import EventTopic, emit_event
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

        try:
            self._record_search()
        except Exception as e:
            logger.warning(f"Stats update (search) failed: {e}")

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
                # Parse legacy "Artist | Title" into structured fields for storage
                sel_artist, sel_title = "", selected_song
                if " | " in selected_song:
                    parts = selected_song.split(" | ", 1)
                    sel_artist, sel_title = parts[0].strip(), parts[1].strip()
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

                        # Determine the next request number (robust if holes exist)
                        try:
                            existing_nums = [int(req.get("RequestNumber", 0)) for req in song_requests if isinstance(req, dict)]
                            next_request_num = (max(existing_nums) + 1) if existing_nums else 1
                        except Exception:
                            next_request_num = len(song_requests) + 1

                        # Get the current system date and time (separate fields expected by GUI)
                        now = datetime.now()
                        current_date = now.strftime("%Y-%m-%d")
                        current_time = now.strftime("%H:%M")

                        # Construct request object (store structured fields only)
                        new_request = {
                            "RequestNumber": next_request_num,
                            "Date": current_date,
                            "Time": current_time,
                            "User": str(interaction.user),
                            "UserId": int(interaction.user.id),  # for future DM/notifications
                            # Future-forward structured fields
                            "Artist": sel_artist,
                            "Title": sel_title,
                        }

                        # Append the new request to the list
                        song_requests.append(new_request)

                        # Save back to the JSON file
                        from utils.helpers import safe_write_json
                        safe_write_json(song_requests_file, song_requests)

                        # Log and confirm using a readable combined form, but do not persist legacy field
                        combined = f"{sel_artist} | {sel_title}" if (sel_artist or sel_title) else selected_song
                        logger.info(f"{interaction.user} requested: {combined} (#{next_request_num})")
                        await interaction.followup.send(
                            f"Added the song to the Song Request List: {combined}"
                        )
                        emit_event(EventTopic.SONG_REQUEST_ADDED, new_request)  # Emit event for new song request
                        # Increment request counters atomically for GUI tracking
                        try:
                            increment_song_request()
                        except Exception as e:
                            logger.warning(f"Stats update (request) failed: {e}")

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
        increment_song_search()

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
