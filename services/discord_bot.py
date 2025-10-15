"""
Discord bot controller/service for managing the Discord bot lifecycle.
"""
import threading
import asyncio
import logging
from typing import Optional

from config.settings import Settings
from utils.logger import get_logger

Settings.initialize()

logger = get_logger(__name__)

class DiscordBotController:
    def __init__(self, bot_class, settings, gui_callbacks=None):
        """
        bot_class: The Discord bot class to instantiate (e.g., DJBot)
        settings: The settings/config object
        gui_callbacks: Optional dict of callbacks for GUI updates (status, error, info, etc.)
        """
        self.bot_class = bot_class
        self.settings = settings
        self.gui_callbacks = gui_callbacks or {}
        self.bot = None
        self.bot_thread = None
        self.is_running = False

    def start_discord_bot(self):
        if self.is_running:
            return
        if not self.settings.get('DISCORD_TOKEN'):
            logger.error("Discord token not found in configuration")
            if self.gui_callbacks and "on_error" in self.gui_callbacks:
                self.gui_callbacks["on_error"]("Discord token not found!")
            return
        logger.info("🚀 Starting Discord bot...")
        logger.debug(f"Bot token configured: {str(self.settings.get('DISCORD_TOKEN'))[:10]}...")
        self.bot_thread = threading.Thread(target=self._run_discord_bot, daemon=True)
        self.bot_thread.start()
        if self.gui_callbacks.get("on_status"):
            self.gui_callbacks["on_status"]("🟡 Starting...", "orange")

    def _run_discord_bot(self):
        loop = None
        try:
            self.is_running = True
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.bot = self.bot_class()
            @self.bot.event
            async def on_ready():
                if self.gui_callbacks.get("on_ready"):
                    self.gui_callbacks["on_ready"](self.bot)
            token = self.settings.get('DISCORD_TOKEN')
            if token:
                loop.run_until_complete(self.bot.start(str(token)))
            else:
                raise ValueError("Discord token not configured")
        except Exception as e:
            logger.error(f"Bot error: {e} | Setup Bot Token in settings.json")
            if self.gui_callbacks.get("on_error"):
                self.gui_callbacks["on_error"](str(e))
        finally:
            self.is_running = False
            if loop and not loop.is_closed():
                try:
                    pending_tasks = asyncio.all_tasks(loop)
                    for task in pending_tasks:
                        task.cancel()
                    if pending_tasks:
                        loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                    loop.close()
                    logger.info("✅ Bot event loop closed properly")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Error during event loop cleanup: {cleanup_error}")
            if self.gui_callbacks.get("on_stopped"):
                self.gui_callbacks["on_stopped"]()

    def stop_discord_bot(self):
        if not self.is_running:
            return
        logger.info("Stopping Discord bot...")
        import warnings, sys, io

        warnings.filterwarnings("ignore", message=".*Unclosed client session.*")
        warnings.filterwarnings("ignore", message=".*Unclosed connector.*")
        warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")
        logging.getLogger('aiohttp').setLevel(logging.CRITICAL)
        original_stderr = sys.stderr
        try:
            sys.stderr = io.StringIO()
            if self.bot and hasattr(self.bot, 'close'):
                if hasattr(self.bot, 'loop') and self.bot.loop and not self.bot.loop.is_closed():
                    future = asyncio.run_coroutine_threadsafe(self.bot.close(), self.bot.loop)
                    try:
                        future.result(timeout=3.0)
                        logger.info("✅ Bot disconnected successfully")
                    except Exception:
                        logger.info("✅ Bot closed")
                else:
                    logger.info("✅ Bot closed")
        except Exception as e:
            if "session" not in str(e).lower():
                logger.error(f"Error stopping bot: {e}")
        finally:
            sys.stderr = original_stderr
        self.is_running = False
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=2.0)
        logger.info("✅ Bot shutdown complete")
        if self.gui_callbacks.get("on_stopped"):
            self.gui_callbacks["on_stopped"]()

    # --- Notifications ---
    def notify_request_played(
        self,
        channel_id: int,
        *,
        artist: str,
        title: str,
        album: Optional[str] = None,
        user_id: Optional[int] = None,
        user_display: Optional[str] = None,
    ) -> None:
        """Post a message to the channel that a requested song is playing.

        If the user is a member of the channel's guild and `user_id` is provided,
        use a proper mention. Otherwise, fall back to a display name without ping.
        """
        try:
            bot = self.bot
            if not self.is_running or bot is None:
                return

            async def _send() -> None:
                try:
                    channel = bot.get_channel(int(channel_id))
                    if channel is None:
                        channel = await bot.fetch_channel(int(channel_id))  # type: ignore[assignment]
                    # Build display text
                    details = f"{artist} - {title}"
                    if album:
                        details += f" [{album}]"
                    # Resolve mention if possible
                    mention_text = None
                    if user_id is not None and hasattr(channel, "guild") and channel.guild is not None:  # type: ignore[attr-defined]
                        member = channel.guild.get_member(int(user_id))  # type: ignore[attr-defined]
                        if member is not None:
                            mention_text = member.mention
                    if mention_text is None:
                        name = user_display or (str(user_id) if user_id is not None else "user")
                        mention_text = f"@{name}"
                    content = f"{mention_text} Your song request ({details}) is playing!!"
                    await channel.send(content)
                except Exception as e:
                    logger.warning(f"Notify request played failed: {e}")

            loop = getattr(bot, "loop", None)
            if loop and not loop.is_closed():
                asyncio.run_coroutine_threadsafe(_send(), loop)
        except Exception:
            pass

    def notify_request_played_multi(
        self,
        channel_id: int,
        *,
        artist: str,
        title: str,
        album: Optional[str] = None,
        users: list[tuple[Optional[int], Optional[str]]] | None = None,
    ) -> None:
        """Post a single message mentioning all requesters for a song.

        Each item in `users` is a tuple of (user_id, user_display). We'll attempt to
        resolve a proper mention for guild members; otherwise fall back to @display text.
        """
        try:
            bot = self.bot
            if not self.is_running or bot is None:
                return

            async def _send() -> None:
                try:
                    channel = bot.get_channel(int(channel_id))
                    if channel is None:
                        channel = await bot.fetch_channel(int(channel_id))  # type: ignore[assignment]

                    details = f"{artist} - {title}"
                    if album:
                        details += f" [{album}]"

                    # Build consolidated mentions
                    mentions: list[str] = []
                    seen: set[str] = set()
                    seq = users or []
                    for uid, display in seq:
                        text: str
                        member_mention: Optional[str] = None
                        try:
                            if uid is not None and hasattr(channel, "guild") and channel.guild is not None:  # type: ignore[attr-defined]
                                m = channel.guild.get_member(int(uid))  # type: ignore[attr-defined]
                                if m is not None:
                                    member_mention = m.mention
                        except Exception:
                            member_mention = None

                        if member_mention:
                            text = member_mention
                        else:
                            fallback = display or (str(uid) if uid is not None else "user")
                            text = f"@{fallback}"

                        key = text.lower()
                        if key not in seen:
                            seen.add(key)
                            mentions.append(text)

                    prefix = " ".join(mentions) if mentions else "@user"
                    content = f"{prefix} | Your song request ({details}) is playing!!"
                    await channel.send(content)
                except Exception as e:
                    logger.warning(f"Notify request played (multi) failed: {e}")

            loop = getattr(bot, "loop", None)
            if loop and not loop.is_closed():
                asyncio.run_coroutine_threadsafe(_send(), loop)
        except Exception:
            pass
