"""
Discord bot controller/service for managing the Discord bot lifecycle.
"""
import threading
import asyncio
from utils.logger import info, debug, warning, error
from config.settings import Settings

Settings.initialize()

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
            error("Discord token not found in configuration")
            if self.gui_callbacks and "on_error" in self.gui_callbacks:
                self.gui_callbacks["on_error"]("Discord token not found!")
            return
        info("🚀 Starting Discord bot...")
        debug(f"Bot token configured: {str(self.settings.get('DISCORD_TOKEN'))[:10]}...")
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
            error(f"Bot error: {e} | Setup Bot Token in settings.json")
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
                    info("✅ Bot event loop closed properly")
                except Exception as cleanup_error:
                    warning(f"⚠️ Error during event loop cleanup: {cleanup_error}")
            if self.gui_callbacks.get("on_stopped"):
                self.gui_callbacks["on_stopped"]()

    def stop_discord_bot(self):
        if not self.is_running:
            return
        info("Stopping Discord bot...")
        import warnings, logging, sys, io
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
                        info("✅ Bot disconnected successfully")
                    except Exception:
                        info("✅ Bot closed")
                else:
                    info("✅ Bot closed")
        except Exception as e:
            if "session" not in str(e).lower():
                error(f"Error stopping bot: {e}")
        finally:
            sys.stderr = original_stderr
        self.is_running = False
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=2.0)
        info("✅ Bot shutdown complete")
        if self.gui_callbacks.get("on_stopped"):
            self.gui_callbacks["on_stopped"]()
