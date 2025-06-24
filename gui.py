"""
Traktor DJ NowPlaying Discord Bot - Standalone GUI Application
A standalone GUI application for running the Traktor DJ NowPlaying Discord Bot with real-time monitoring.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import queue
import os
from datetime import datetime
import asyncio
import io

# Import the centralized logger
from utils.logger import set_gui_callback, set_debug_mode, info, debug, warning, error

# Setup for PyInstaller executable - MUST be done before any local imports
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    exe_dir = os.path.dirname(sys.executable)
    os.chdir(exe_dir)  # Change to executable directory for .env file access
    
    # Add the PyInstaller bundle directory to Python path
    bundle_dir = getattr(sys, '_MEIPASS', exe_dir)
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

def check_and_create_env_file():
    """Check for .env file and create from template if missing"""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        # Default .env template content
        example_content = """# Example environment file for Traktor DJ NowPlaying Discord Bot
# Copy this to .env and fill in your actual values

# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
APPLICATION_ID=your_application_id_here

# Discord Channel and User Permissions (comma-separated)
CHANNEL_IDS=channel_id_1,channel_id_2
ALLOWED_USER_IDS=user_id_1,user_id_2

# Live Notification Roles (optional, comma-separated role names)
DISCORD_LIVE_NOTIFICATION_ROLES=Tunes,DJ Friends,Music Lovers

#Location of root Traktor folder (ie without the version number)
TRAKTOR_LOCATION=C:\\Users\\YourUser\\Documents\\Native Instruments\\
TRAKTOR_COLLECTION_FILENAME=collection.nml

#Location of Now Playing configuration file
NOWPLAYING_CONFIG_JSON_PATH=C:\\Users\\YourUser\\.nowplaying\\config.json

#Location of Song Requests file (optional - defaults to song_requests.json in current directory)
#SONG_REQUESTS_FILE=song_requests.json
"""
        
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(example_content)
            
            # Show user-friendly message and exit
            messagebox.showinfo(
                "Setup Required - .env File Created",
                ".env configuration file has been created!\n\n"
                "📝 Please edit the .env file and replace the placeholder values with your actual settings:\n\n"
                "• DISCORD_TOKEN - Your Discord bot token\n"
                "• APPLICATION_ID - Your Discord application ID\n"
                "• CHANNEL_IDS - Channel IDs (numbers, comma-separated)\n"
                "• ALLOWED_USER_IDS - User IDs (numbers, comma-separated)\n"
                "• TRAKTOR_LOCATION - Path to your Traktor folder\n"
                "• NOWPLAYING_CONFIG_JSON_PATH - Path to Now Playing config\n\n"
                "💡 Once configured, relaunch this application to start the bot.\n\n"
                "Click OK to close this application."
            )
            
            return False  # Signal to exit application
        except Exception as e:
            messagebox.showerror("Error", f"Could not create .env file: {e}")
            return None
    
    return True  # File exists

def check_env_file_configured():
    """Check if .env file has been properly configured (not using template values)"""
    try:
        from dotenv import load_dotenv
        import os
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Check for template values that indicate unconfigured .env
        token = os.getenv('DISCORD_TOKEN', '').strip()
        app_id = os.getenv('APPLICATION_ID', '').strip()
        channels = os.getenv('CHANNEL_IDS', '').strip()
        users = os.getenv('ALLOWED_USER_IDS', '').strip()
        
        template_values = [
            'your_discord_bot_token_here',
            'your_application_id_here', 
            'channel_id_1',
            'user_id_1'
        ]
        
        # Check if any template values are still present
        if (token in template_values or 
            app_id in template_values or 
            'channel_id_1' in channels or 
            'user_id_1' in users):
            
            messagebox.showwarning(
                "Configuration Required",
                ".env file exists but contains template values!\n\n"
                "📝 Please edit the .env file and replace ALL placeholder values with your actual settings.\n\n"
                "The application will now close so you can configure the .env file.\n\n"
                "Relaunch after making your changes."
            )
            return False
            
    except Exception as e:
        messagebox.showerror("Configuration Error", f"Error checking .env configuration: {e}")
        return False
    
    return True

# Check and create .env file if needed
env_status = check_and_create_env_file()

# If .env was just created, exit to let user configure it
if env_status is False:
    sys.exit(0)
elif env_status is None:
    sys.exit(1)

# Check if .env is properly configured
if not check_env_file_configured():
    sys.exit(0)

# Import the bot and version
try:
    from main import DJBot
    from config.settings import Settings
    try:
        from version import __version__
    except ImportError:
        __version__ = "dev"
except ImportError as e:
    # Handle import errors gracefully for GUI-only executables
    __version__ = "unknown"
    
    # More user-friendly error message for executable
    if getattr(sys, 'frozen', False):
        error_msg = "Setup Error: Could not load bot modules.\n\nThis may be due to missing dependencies or configuration issues."
    else:
        error_msg = f"Error importing bot modules: {e}\nPlease ensure you're running from the correct directory."
    
    try:
        # Try to show GUI error dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror("Setup Error", error_msg)
        root.destroy()
    except:
        # Falleback to print if GUI isn't available
        print(f"Error importing bot modules: {e}")
        print("Please ensure you're running from the correct directory.")
    sys.exit(1)


class BotGUI:
    """GUI application for the Traktor DJ NowPlaying Discord Bot"""
    
    def __init__(self, title=None):
        from services.discord_bot import DiscordBotController
        from main import DJBot
        from config.settings import Settings
        self.discord_bot_controller = DiscordBotController(
            bot_class=DJBot,
            settings=Settings,
            gui_callbacks={
                "on_ready": self.on_discord_bot_ready,
                "on_status": lambda text, color: self.status_label.config(text=text, foreground=color),
                "on_error": self.on_discord_bot_error,
                "on_stopped": self.on_discord_bot_stopped
            }
        )
        self.debug_mode = '--debug' in sys.argv
        self.root = tk.Tk()
        app_title = title or f"Traktor DJ NowPlaying Discord Bot v{__version__} - Control Panel"
        self.root.title(app_title)
        self.root.geometry("1200x700")  # Widened for new layout
        self.root.minsize(1000, 500)
        # Set window icon - remove the janky black diamond/question mark icon
        try:
            # Use PyInstaller's _MEIPASS for bundled resources
            if getattr(sys, 'frozen', False):
                bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
                icon_path = os.path.join(bundle_dir, 'app_icon.ico')
                png_icon_path = os.path.join(bundle_dir, 'icon.png')
            else:
                icon_path = 'app_icon.ico'
                png_icon_path = 'icon.png'
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                info(f"✅ Using custom icon: {icon_path}")
            elif os.path.exists(png_icon_path):
                icon_image = tk.PhotoImage(file=png_icon_path)
                self.root.iconphoto(True, icon_image)
                info(f"✅ Using PNG icon: {png_icon_path}")
            else:
                self.root.wm_iconbitmap('')
                info("ℹ️  Removed default icon - no custom icon found")
        except Exception as e:
            warning(f"⚠️  Could not set custom icon: {e}")
            try:
                self.root.wm_iconbitmap('')
            except:
                pass
        
        # Set up global warning filters for aiohttp cleanup messages
        import warnings
        warnings.filterwarnings("ignore", message=".*Unclosed client session.*")
        warnings.filterwarnings("ignore", message=".*Unclosed connector.*")
        warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")
        
        # Bot instance
        self.bot = None
        self.bot_task = None
        self.is_running = False
        self.bot_thread = None
        self.search_count = 0
        self.output_queue = queue.Queue()
        self.setup_gui()
        self.setup_output_capture()
        set_gui_callback(self.add_log)
        from config.settings import Settings
        set_debug_mode(Settings.DEBUG)
        info("GUI logger callback initialized")
        debug("Debug mode is enabled" if Settings.DEBUG else "Debug mode is disabled")
        self.check_output_queue()
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        self.root.protocol("WM_DELETE_WINDOW", self.on_x_button_clicked)
        # Always enable all GUI features, but only block Discord bot connection in debug mode
        if not self.debug_mode:
            self.root.after(1000, self.auto_start_bot)
        else:
            info("Debug mode enabled: Bot will not connect to Discord.")
            self.status_label.config(text="🟡 Debug Mode (Bot Not Connected)", foreground="orange")
            # Optionally, load collection stats and other features for testing
            self.load_collection_stats()
    
    def setup_gui(self):
        """Set up the GUI elements"""
        # Configure the root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=3)  # Console/NowPlaying area
        main_frame.columnconfigure(2, weight=2)  # Song Requests area
        main_frame.columnconfigure(0, weight=0)  # Controls don't expand
        main_frame.rowconfigure(1, weight=1)
        # Removed the large title label to save space
        
        # Left panel - Controls
        from gui_components.gui_controls_stats import ControlsStatsPanel
        # Check if NowPlaying is enabled
        from config.settings import Settings
        self.nowplaying_enabled = Settings.is_nowplaying_enabled()
        # Define button texts for dynamic sizing (conditionally include NowPlaying button)
        button_texts = [
            "🛑 Stop & Close",
            "🗑️ Clear Log", 
            "🔄 Refresh Collection & Stats"
        ]
        if self.nowplaying_enabled:
            button_texts.append("🧹 Clear NP Track Info")
        # Use the class method for initial calculation before panel exists
        from gui_components.gui_controls_stats import ControlsStatsPanel
        optimal_width = ControlsStatsPanel.calculate_optimal_button_width(button_texts)
        self.controls_stats_panel = ControlsStatsPanel(
            main_frame,
            button_texts,
            optimal_width,
            self.nowplaying_enabled,
            self.clear_log,
            self.refresh_session_stats,
            self.reset_global_stats,
            self.clear_track_history,
            self.on_stop_button_press,
            self.on_stop_button_release
        )
        self.controls_stats_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 15))
        # Expose key widgets for BotGUI
        self.stop_button = self.controls_stats_panel.stop_button
        self.status_label = self.controls_stats_panel.status_label
        self.bot_name_label = self.controls_stats_panel.bot_name_label
        self.bot_id_label = self.controls_stats_panel.bot_id_label
        self.commands_label = self.controls_stats_panel.commands_label
        self.import_title_label = self.controls_stats_panel.import_title_label
        self.import_date_label = self.controls_stats_panel.import_date_label
        self.import_time_label = self.controls_stats_panel.import_time_label
        self.songs_label = self.controls_stats_panel.songs_label
        self.new_songs_label = self.controls_stats_panel.new_songs_label
        self.session_searches_label = self.controls_stats_panel.session_searches_label
        self.total_searches_label = self.controls_stats_panel.total_searches_label
        
        # Console/NowPlaying Panel (was right_panel)
        console_panel = ttk.Frame(main_frame)
        console_panel.grid(row=1, column=1, sticky="nsew")
        console_panel.columnconfigure(0, weight=1)
        console_panel.rowconfigure(0, weight=1)  # Now Playing (top half)
        console_panel.rowconfigure(1, weight=1)  # Log (bottom half)

        # Now Playing Panel (top half of console_panel)
        from gui_components.gui_nowplaying import NowPlayingPanel
        self.nowplaying_panel = NowPlayingPanel(console_panel)
        self.nowplaying_panel.grid(row=0, column=0, sticky="nsew")

        # Log Panel (bottom half of console_panel)
        from gui_components.gui_logconsole import LogConsolePanel
        self.log_console_panel = LogConsolePanel(console_panel)
        self.log_console_panel.grid(row=1, column=0, sticky="nsew")
        self.output_text = self.log_console_panel.output_text

        # Song Requests Panel (new, right of console/log)
        from gui_components.gui_songrequests import SongRequestsPanel
        self.song_requests_panel = SongRequestsPanel(main_frame)
        self.song_requests_panel.grid(row=1, column=2, sticky="nsew", padx=(15, 0))  # Add left padding
        # Bring window to front on song request add/delete
        from utils.events import subscribe
        subscribe("song_request_added", lambda _: self.bring_to_front())
        subscribe("song_request_deleted", lambda _: self.bring_to_front())

        # Add initial message
        info("🎛️ Traktor DJ NowPlaying Discord Bot Control Panel initialized")
        info("⏱️ Auto-startup scheduled in 1 second...")
        
        # Show GUI
        self.root.deiconify()  # Show the window
    
    def setup_output_capture(self):
        """Set up output capture for stdout and stderr using OutputCapture from logger.py"""
        from utils.logger import OutputCapture
        self.original_stdout = sys.stdout if sys.stdout is not None else sys.__stdout__
        self.original_stderr = sys.stderr if sys.stderr is not None else sys.__stderr__
        import io
        # Ensure we have valid streams
        if self.original_stdout is None:
            self.original_stdout = io.StringIO()
        if self.original_stderr is None:
            self.original_stderr = io.StringIO()
        # Create capture objects - these will intercept ALL output
        self.stdout_capture = OutputCapture(self.output_queue, "info", self.original_stdout, self)
        self.stderr_capture = OutputCapture(self.output_queue, "error", self.original_stderr, self)
        # Output capture is now ready - subsequent print statements will appear in GUI
    
    def add_log(self, message, level="info"):
        self.log_console_panel.add_log(message, level)

    def check_output_queue(self):
        """Check for new output from the bot"""
        try:
            while True:
                tag, message = self.output_queue.get_nowait()
                # Minimal filtering - only skip very technical/noisy messages
                skip_messages = [
                    "heartbeat", "websocket received", "dispatching event", 
                    "keep-alive", "ssl handshake"
                ]
                
                # Show most messages to match terminal output
                if not any(skip in message.lower() for skip in skip_messages):
                    clean_message = message.strip()
                    if clean_message:
                        # Determine appropriate log level based on content
                        if any(word in clean_message.lower() for word in ["error", "failed", "exception", "traceback"]):
                            level = "error"
                        elif any(word in clean_message.lower() for word in ["warning", "warn"]):
                            level = "warning"
                        elif any(word in clean_message.lower() for word in ["ready", "online", "connected", "success", "✅"]):
                            level = "success"
                        else:
                            level = tag
                        
                        self.add_log(clean_message, level)
        except queue.Empty:
            pass
        
        # Update search count display
        self.update_search_count_display()
        
        # Schedule next check        self.root.after(100, self.check_output_queue)

    def auto_start_bot(self):
        """Automatically start the Discord bot on launch"""
        if self.is_running:
            debug("Auto-startup skipped - bot already running")
            return
        debug("Auto-startup enabled - initiating bot start")
        self.start_discord_bot()

    def start_discord_bot(self):
        """Start the Discord bot"""
        if getattr(self, 'debug_mode', False):
            info("Debug mode: Skipping Discord bot connection.")
            self.status_label.config(text="🟡 Debug Mode (Bot Not Connected)", foreground="orange")
            return
        self.discord_bot_controller.start_discord_bot()

    def stop_discord_bot(self):
        """Stop the Discord bot immediately"""
        self.discord_bot_controller.stop_discord_bot()

    def on_stop_button_press(self, event=None):
        """Show stopping message when stop button is pressed down or X is clicked"""
        self.add_log("Stop button pressed - preparing to close...", "warning")

    def on_stop_button_release(self, event=None):
        """Execute stop and close when button is released"""
        self._shutdown_application()

    def on_x_button_clicked(self):
        """Always prompt for confirmation when X is clicked. Only proceed if user confirms."""
        result = messagebox.askyesno(
            "Confirm Exit",
            "Are you sure you want to exit the application?\n\nIf the bot is running, it will be stopped."
        )
        if result:
            info("🔄 User requested application close - stopping bot (if running)...")
            self._shutdown_application()
        else:
            info("Exit cancelled by user.")

    def update_controls_frame_sizing(self):
        if hasattr(self, 'controls_stats_panel'):
            self.controls_stats_panel.update_controls_frame_sizing(self.nowplaying_enabled)

    def _shutdown_application(self):
        """Common shutdown logic for both Stop button and X button"""
        if self.is_running:
            info("🔄 User requested application close - stopping bot...")
            self.stop_discord_bot()
            # Wait for clean shutdown then close
            self.root.after(500, self.root.destroy)
        else:
            info("🔄 Closing application...")
            self.root.destroy()

    def clear_log(self):
        """Clear the output log via the log console panel."""
        if hasattr(self, 'log_console_panel'):
            self.log_console_panel.clear_log()

    def clear_track_history(self):
        """Clear track history in NowPlaying config.json using the utility function."""
        from config.settings import Settings
        from utils.nowplaying import clear_nowplaying_track_history
        if not Settings.is_nowplaying_enabled():
            warning("❌ NowPlaying integration is not enabled")
            return
        if not Settings.NOWPLAYING_CONFIG_JSON_PATH:
            warning("❌ Config file path not set in environment variable NOWPLAYING_CONFIG_JSON_PATH")
            return
        success = clear_nowplaying_track_history(Settings.NOWPLAYING_CONFIG_JSON_PATH)
        if not success:
            error("❌ Failed to clear NowPlaying track history.")
        # Optionally, update the GUI or show a messagebox if you want user feedback

    def refresh_collection(self):
        """Refresh the Traktor collection by copying the latest file and reloading stats"""
        def _refresh():
            try:
                from config.settings import Settings
                from utils.traktor import initialize_collection
                result = initialize_collection(
                    Settings.TRAKTOR_PATH,
                    Settings.COLLECTION_JSON_FILE,
                    Settings.EXCLUDED_ITEMS,
                    Settings.NEW_SONGS_DAYS,
                    Settings.MAX_SONGS,
                    debug_mode=Settings.DEBUG
                )
                if result["success"]:
                    info(f"✅ Collection refreshed successfully - {result['total_songs']:,} songs processed")
                    self.update_search_count_display()
                    self.root.after(0, lambda: self.songs_label.config(text=f"Songs: {result['total_songs']:,}"))
                    self.root.after(0, lambda: self.new_songs_label.config(text=f"New Songs: {result['total_new_songs']:,}"))
                    self.root.after(0, lambda: self.import_date_label.config(text=result['date_str']))
                    self.root.after(0, lambda: self.import_time_label.config(text=result['time_str']))
                    self.root.after(50, self.update_controls_frame_sizing)
                else:
                    warning(f"⚠️ {result['error_msg']}")
                    self.root.after(0, lambda: self.songs_label.config(text="Songs: Collection not found"))
                    self.root.after(0, lambda: self.new_songs_label.config(text="New Songs: Collection not found"))
            except Exception as e:
                error_msg = f"Error refreshing collection: {e}"
                error(error_msg)
        threading.Thread(target=_refresh, daemon=True).start()

    def load_collection_stats(self):
        """Load and display collection statistics"""
        def _load_stats():
            try:
                from config.settings import Settings
                from utils.traktor import initialize_collection
                import os
                # Only load stats if JSON exists, otherwise refresh
                if not os.path.exists(Settings.COLLECTION_JSON_FILE):
                    warning("Collection JSON not found, creating from Traktor collection...")
                result = initialize_collection(
                    Settings.TRAKTOR_PATH,
                    Settings.COLLECTION_JSON_FILE,
                    Settings.EXCLUDED_ITEMS,
                    Settings.NEW_SONGS_DAYS,
                    Settings.MAX_SONGS,
                    debug_mode=Settings.DEBUG
                )
                if result["success"]:
                    info(f"📊 Collection stats: {result['total_songs']:,} total songs, {result['total_new_songs']:,} new songs (last {Settings.NEW_SONGS_DAYS} days)")
                    self.root.after(0, lambda: self.songs_label.config(text=f"Songs: {result['total_songs']:,}"))
                    self.root.after(0, lambda: self.new_songs_label.config(text=f"New Songs: {result['total_new_songs']:,}"))
                    self.root.after(0, lambda: self.import_date_label.config(text=result['date_str']))
                    self.root.after(0, lambda: self.import_time_label.config(text=result['time_str']))
                    self.root.after(50, self.update_controls_frame_sizing)
                else:
                    warning(f"⚠️ {result['error_msg']}")
                    self.root.after(0, lambda: self.songs_label.config(text="Songs: Collection not found"))
                    self.root.after(0, lambda: self.new_songs_label.config(text="New Songs: Collection not found"))
                    self.root.after(0, lambda: self.import_date_label.config(text="Not available"))
                    self.root.after(0, lambda: self.import_time_label.config(text=""))
            except Exception as e:
                error_msg = f"Error loading collection stats: {e}"
                print(f"❌ {error_msg}")
                self.root.after(0, lambda: self.songs_label.config(text="Songs: Error loading"))
                self.root.after(0, lambda: self.new_songs_label.config(text="New Songs: Error loading"))
                self.root.after(0, lambda: self.import_date_label.config(text="Error"))
                self.root.after(0, lambda: self.import_time_label.config(text=""))
        threading.Thread(target=_load_stats, daemon=True).start()

    def update_search_count_display(self):
        """Update the search count labels in the GUI using stats.json."""
        from utils.stats import load_stats
        stats = load_stats()
        session_count = stats.get("session_song_searches", 0)
        total_count = stats.get("total_song_searches", 0)
        self.root.after(0, lambda: self.session_searches_label.config(text=f"Song Searches (Session): {session_count}"))
        self.root.after(0, lambda: self.total_searches_label.config(text=f"Total Song Searches: {total_count}"))

    def on_discord_bot_ready(self, bot):
        """Update bot information in the UI when the Discord bot is ready."""
        self.status_label.config(text="🟢 Discord Bot Online", foreground="green")
        self.bot_name_label.config(text=f"Name: {bot.user}")
        self.bot_id_label.config(text=f"ID: {bot.user.id}")
        command_count = len([cmd for cmd in bot.tree.walk_commands()])
        self.commands_label.config(text=f"Commands: {command_count} loaded")
        self.load_collection_stats()

    def on_discord_bot_error(self, error_msg):
        """Handle Discord bot errors."""
        self.status_label.config(text="🔴 Discord  Bot Error", foreground="red")
        messagebox.showerror("Bot Error", f"Bot encountered an error:\n{error_msg}")

    def on_discord_bot_stopped(self):
        """Handle Discord bot stopping."""
        self.status_label.config(text="⚪ Discord  Bot Stopped", foreground="gray")
        self.stop_button.config(state='disabled')
        self.bot_name_label.config(text="Name: Not connected")
        self.bot_id_label.config(text="ID: Not connected")
        self.commands_label.config(text="Commands: Not loaded")
        self.songs_label.config(text="Songs: Not loaded")
        self.new_songs_label.config(text="New Songs: Not loaded")
        self.reset_global_button.config(command=self.reset_global_stats)

        # Expose refresh button for session stats
        self.refresh_button = self.controls_stats_panel.refresh_button
        self.reset_global_button = self.controls_stats_panel.reset_global_button
        # Set the correct command for the buttons
        self.refresh_button.config(command=self.refresh_session_stats)
        self.reset_global_button.config(command=self.reset_global_stats)

    def refresh_session_stats(self):
        """Refresh Traktor collection, then reset session stats."""
        from utils.stats import reset_session_stats
        info(f"🔄 Refresh Session Stats button pressed.")
        reset_session_stats()
        info("🔄 Refresh Session Stats - refreshing Traktor collection...")
        self.refresh_collection()
        self.update_search_count_display()

    def reset_global_stats(self):
        """Reset all global stats (persistent) with confirmation dialog."""
        from utils.stats import reset_global_stats
        info(f"🔄 Reset of Global Stats button pressed.")
        result = messagebox.askyesno(
            "Confirm Global Stats Reset",
            "Are you sure you want to reset ALL global stats?\n\nThis cannot be undone!"
        )
        if result:
            info(f"🧹 Reset Global Stats button pressed.")
            reset_global_stats()
            self.update_search_count_display()
        else:
            info("Reset Global Stats cancelled by user.")

    def bring_to_front(self):
        try:
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(200, lambda: self.root.attributes('-topmost', False))
        except Exception:
            pass

    def run(self):
        """Run the Tkinter GUI loop"""
        self.root.mainloop()

# Start the GUI application
def run_gui():
    """Run the Tkinter GUI loop"""
    try:
        app = BotGUI()
        app.run()
    except Exception as e:
        # Handle any uncaught exceptions in the GUI
        error_msg = f"Unexpected error in GUI: {e}"
        print(f"❌ {error_msg}")
        try:
            messagebox.showerror("Unexpected Error", error_msg)
        except:
            pass  # Ignore errors in the error handler itself

if __name__ == "__main__":
    run_gui()
