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
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Traktor DJ NowPlaying Discord Bot v{__version__} - Control Panel")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)        # Set window icon - remove the janky black diamond/question mark icon
        try:
            # First try to use a custom .ico file if available
            icon_path = 'app_icon.ico'
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                print(f"✅ Using custom icon: {icon_path}")
            else:
                # Try PNG icon as PhotoImage
                png_icon_path = 'icon.png'
                if os.path.exists(png_icon_path):
                    # Load and use PNG icon
                    icon_image = tk.PhotoImage(file=png_icon_path)
                    self.root.iconphoto(True, icon_image)
                    print(f"✅ Using PNG icon: {png_icon_path}")
                else:
                    # Remove the default janky icon by setting empty
                    self.root.wm_iconbitmap('')
                    print("ℹ️  Removed default icon - no custom icon found")
        except Exception as e:
            print(f"⚠️  Could not set custom icon: {e}")
            try:
                # Fallback - try to remove default icon
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
          # Search counter
        self.search_count = 0
        self.load_search_count()
        
        # Threading
        self.output_queue = queue.Queue()
        
        # Set up the GUI
        self.setup_gui()
        self.setup_output_capture()        # Start checking for output updates
        self.check_output_queue()
        
        # Start output capture immediately
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-start the bot after GUI is ready
        self.root.after(1000, self.auto_start_bot)
    
    def setup_gui(self):
        """Set up the GUI elements"""
        # Configure the root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
          # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=3)  # Give log more weight
        main_frame.columnconfigure(0, weight=0)  # Controls don't expand
        main_frame.rowconfigure(1, weight=1)
          # Title
        title_label = ttk.Label(
            main_frame, 
            text="Traktor DJ NowPlaying Discord Bot Control Panel", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Left panel - Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 15))
        
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
            button_texts.append("🧹 Clear NP Track Info")        # Calculate optimal button width
        optimal_width = self.calculate_optimal_button_width(button_texts)# Configure controls frame - no expansion, let content determine size
        controls_frame.columnconfigure(0, weight=0)  # Don't expand
        # Set a reasonable fixed width based on button content
        controls_frame.grid_columnconfigure(0, minsize=200)  # Conservative fixed width
          # Control buttons (Start Bot removed - now auto-starts)
        self.stop_button = ttk.Button(
            controls_frame,
            text=button_texts[0],
            width=optimal_width,
            state='disabled'
        )
        # Bind separate events for press and release
        self.stop_button.bind('<Button-1>', self.on_stop_button_press)
        self.stop_button.bind('<ButtonRelease-1>', self.on_stop_button_release)
        self.stop_button.grid(row=0, column=0, pady=8)
        
        # Status section
        status_frame = ttk.LabelFrame(controls_frame, text="Status", padding="10")
        status_frame.grid(row=2, column=0, pady=(15, 10), sticky="ew")
        
        self.status_label = ttk.Label(status_frame, text="⚪ Bot Stopped")
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Bot info section
        info_frame = ttk.LabelFrame(controls_frame, text="Bot Information", padding="10")
        info_frame.grid(row=3, column=0, pady=10, sticky="ew")
        
        self.bot_name_label = ttk.Label(info_frame, text="Name: Not connected")
        self.bot_name_label.grid(row=0, column=0, sticky="w")
        
        self.bot_id_label = ttk.Label(info_frame, text="ID: Not connected")
        self.bot_id_label.grid(row=1, column=0, sticky="w")
        
        self.commands_label = ttk.Label(info_frame, text="Commands: Not loaded")
        self.commands_label.grid(row=2, column=0, sticky="w")        # Statistics section
        stats_frame = ttk.LabelFrame(controls_frame, text="Collection Stats", padding="10")
        stats_frame.grid(row=4, column=0, pady=10, sticky="ew")
        
        # Traktor Import (first item, special formatting)
        self.import_title_label = ttk.Label(stats_frame, text="Traktor Import:", font=("Arial", 9, "bold"))
        self.import_title_label.grid(row=0, column=0, sticky="w")
        
        self.import_date_label = ttk.Label(stats_frame, text="Loading...", font=("Arial", 8))
        self.import_date_label.grid(row=1, column=0, sticky="w", padx=(10, 0))
        
        self.import_time_label = ttk.Label(stats_frame, text="", font=("Arial", 8))
        self.import_time_label.grid(row=2, column=0, sticky="w", padx=(10, 0))
        
        # Other stats
        self.songs_label = ttk.Label(stats_frame, text="Songs: Loading...")
        self.songs_label.grid(row=3, column=0, sticky="w", pady=(5, 0))
        
        self.new_songs_label = ttk.Label(stats_frame, text="New Songs: Loading...")
        self.new_songs_label.grid(row=4, column=0, sticky="w")
        
        self.searches_label = ttk.Label(stats_frame, text="Song Searches: 0")
        self.searches_label.grid(row=5, column=0, sticky="w")
        
        # Clear log button
        clear_button = ttk.Button(
            controls_frame,
            text=button_texts[1],
            command=self.clear_log,
            width=optimal_width
        )
        clear_button.grid(row=5, column=0, pady=(15, 8))        # Refresh collection button with better styling
        refresh_button = ttk.Button(
            controls_frame,
            text=button_texts[2],
            command=self.refresh_collection,
            width=optimal_width
        )
        refresh_button.grid(row=6, column=0, pady=8)        # Clear NP track info button (only if NowPlaying is enabled)
        if self.nowplaying_enabled:
            clear_history_button = ttk.Button(
                controls_frame,
                text=button_texts[3],
                command=self.clear_track_history,
                width=optimal_width
            )
            clear_history_button.grid(row=7, column=0, pady=8)
        
        # Right panel - Log
        log_frame = ttk.LabelFrame(main_frame, text="Bot Output Log", padding="8")
        log_frame.grid(row=1, column=1, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Output text area with scrollbar
        self.output_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=60,
            height=25,
            font=("Consolas", 10),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#404040"
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure text tags for colored output
        self.output_text.tag_configure("info", foreground="#ffffff")
        self.output_text.tag_configure("success", foreground="#4CAF50")
        self.output_text.tag_configure("warning", foreground="#FF9800")
        self.output_text.tag_configure("error", foreground="#f44336")
        self.output_text.tag_configure("timestamp", foreground="#888888")        # Add initial message
        self.add_log("Traktor DJ NowPlaying Discord Bot Control Panel initialized", "info")
        self.add_log("Auto-starting bot in 1 second...", "info")
        
        # Show GUI
        self.root.deiconify()  # Show the window
    
    def setup_output_capture(self):
        """Set up output capture for stdout and stderr"""
        class OutputCapture:
            def __init__(self, queue_obj, tag, original, gui_instance):
                self.queue = queue_obj
                self.tag = tag
                self.original = original
                self.gui = gui_instance
            
            def write(self, text):
                # Always write to original first (terminal) - this ensures terminal gets everything
                self.original.write(text)
                self.original.flush()
                
                # Then capture for GUI (only non-empty lines)
                if text.strip():
                    self.queue.put((self.tag, text.strip()))
            
            def flush(self):
                self.original.flush()        # Store original streams (handle None case for PyInstaller)
        self.original_stdout = sys.stdout if sys.stdout is not None else sys.__stdout__
        self.original_stderr = sys.stderr if sys.stderr is not None else sys.__stderr__
        
        # Ensure we have valid streams
        if self.original_stdout is None:
            # Create a dummy stream for PyInstaller GUI mode
            import io
            self.original_stdout = io.StringIO()
        if self.original_stderr is None:
            import io
            self.original_stderr = io.StringIO()
        
        # Create capture objects - these will intercept ALL output
        self.stdout_capture = OutputCapture(self.output_queue, "info", self.original_stdout, self)
        self.stderr_capture = OutputCapture(self.output_queue, "error", self.original_stderr, self)
        
        # Output capture is now ready - subsequent print statements will appear in GUI
    
    def add_log(self, message, level="info"):
        """Add a message to the log with timestamp and color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insert timestamp
        self.output_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Insert message with appropriate color
        self.output_text.insert(tk.END, f"{message}\n", level)
          # Auto-scroll to bottom
        self.output_text.see(tk.END)
        
        # Limit log size (keep last 1000 lines)
        lines = self.output_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:
            lines_to_delete = len(lines) - 1000
            self.output_text.delete("1.0", f"{lines_to_delete}.0")
    
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
        
        # Schedule next check
        self.root.after(100, self.check_output_queue)
    
    def auto_start_bot(self):
        """Automatically start the bot on launch"""
        print("🤖 Auto-starting Discord bot...")
        self.start_bot()
    
    def start_bot(self):
        """Start the Discord bot"""
        if self.is_running:
            return
        
        try:            # Validate configuration
            if not Settings.TOKEN:
                messagebox.showerror(
                    "Configuration Error",
                    "Discord token not found!\n\nPlease check your .env file and ensure DISCORD_TOKEN is set."
                )
                return
            
            print("🚀 Starting Discord bot...")
            
            # Start bot in separate thread
            self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
            self.bot_thread.start()
            
            # Update UI (Start button removed - using auto-start now)
            self.stop_button.config(state='normal')
            self.status_label.config(text="🟡 Starting...", foreground="orange")
            
        except Exception as e:
            self.add_log(f"Error starting bot: {e}", "error")
            messagebox.showerror("Startup Error", f"Failed to start bot:\n{e}")
    
    def _run_bot(self):
        """Run the bot in a separate thread"""
        loop = None
        try:
            self.is_running = True
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create bot instance
            self.bot = DJBot()
            
            # Set up bot event handlers
            @self.bot.event
            async def on_ready():
                # Update UI from main thread
                self.root.after(0, self._update_bot_info)
            
            # Run the bot
            if Settings.TOKEN:
                loop.run_until_complete(self.bot.start(Settings.TOKEN))
            else:
                raise ValueError("Discord TOKEN not configured")
                
        except Exception as e:
            self.add_log(f"Bot error: {e}", "error")
            self.root.after(0, self._handle_bot_error, str(e))
        finally:
            self.is_running = False
            
            # Properly close the event loop
            if loop and not loop.is_closed():
                try:
                    # Cancel all pending tasks
                    pending_tasks = asyncio.all_tasks(loop)
                    for task in pending_tasks:
                        task.cancel()
                    
                    # Wait for tasks to complete cancellation
                    if pending_tasks:
                        loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                    
                    # Close the loop
                    loop.close()
                    print("✅ Bot event loop closed properly")
                except Exception as cleanup_error:
                    print(f"⚠️ Error during event loop cleanup: {cleanup_error}")
            
            self.root.after(0, self._bot_stopped)
    
    def _update_bot_info(self):
        """Update bot information in the UI"""
        if self.bot and self.bot.user:
            self.status_label.config(text="🟢 Bot Online", foreground="green")
            self.bot_name_label.config(text=f"Name: {self.bot.user}")
            self.bot_id_label.config(text=f"ID: {self.bot.user.id}")
              # Count commands
            command_count = len([cmd for cmd in self.bot.tree.walk_commands()])
            self.commands_label.config(text=f"Commands: {command_count} loaded")            
            # Print to both terminal and GUI (using print so it goes through output capture)
            print("🎵 Traktor DJ NowPlaying Discord Bot Loaded")
            print(f"🤖 Logged in as {self.bot.user} (ID: {self.bot.user.id})")
            print(f"✅ Loaded {command_count} slash commands")
            print("✅ Bot is ready and operational!")
              # Refresh collection stats when bot comes online
            self.initialize_collection_on_startup()
    
    def _handle_bot_error(self, error_msg):
        """Handle bot errors"""
        self.status_label.config(text="🔴 Bot Error", foreground="red")
        messagebox.showerror("Bot Error", f"Bot encountered an error:\n{error_msg}")
    
    def _bot_stopped(self):
        """Handle bot stopping"""
        self.status_label.config(text="⚪ Bot Stopped", foreground="gray")
        # Start button removed - bot will auto-restart if GUI is restarted
        self.stop_button.config(state='disabled')
        
        # Reset bot info
        self.bot_name_label.config(text="Name: Not connected")
        self.bot_id_label.config(text="ID: Not connected")
        self.commands_label.config(text="Commands: Not loaded")
        self.songs_label.config(text="Songs: Not loaded")
        self.new_songs_label.config(text="New Songs: Not loaded")
          # Restore output
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def stop_bot(self):
        """Stop the Discord bot immediately"""
        if not self.is_running:
            return
        
        self.add_log("Stopping bot...", "warning")        # Permanently suppress aiohttp warnings using warnings filter
        import warnings
        import logging
        
        # Add filters to permanently suppress aiohttp warnings
        warnings.filterwarnings("ignore", message=".*Unclosed client session.*")
        warnings.filterwarnings("ignore", message=".*Unclosed connector.*")
        warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")
        
        # Also suppress them at the logging level
        logging.getLogger('aiohttp').setLevel(logging.CRITICAL)
        
        # Temporarily suppress stderr during the actual shutdown process
        original_stderr = sys.stderr
        try:
            # Redirect stderr to suppress any remaining console output
            import io
            sys.stderr = io.StringIO()
            
            if self.bot and hasattr(self.bot, 'close'):
                # Create a new event loop to properly close the bot
                if hasattr(self.bot, 'loop') and self.bot.loop and not self.bot.loop.is_closed():
                    # Schedule the close operation in the bot's event loop
                    future = asyncio.run_coroutine_threadsafe(self.bot.close(), self.bot.loop)
                    # Wait for the close operation to complete (with timeout)
                    try:
                        future.result(timeout=3.0)  # Reduced timeout
                        print("✅ Bot disconnected successfully")
                    except Exception:
                        # Suppress timeout/error messages - bot is closing anyway
                        print("✅ Bot closed")
                else:
                    print("✅ Bot closed")
                    
        except Exception as e:
            # Only show critical errors, suppress session-related messages
            if "session" not in str(e).lower():
                self.add_log(f"Error stopping bot: {e}", "error")
        finally:
            # Restore stderr (warnings filters remain active permanently)
            sys.stderr = original_stderr
        
        # Mark as not running immediately
        self.is_running = False
        
        # Give the bot thread a moment to clean up (simplified output)
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=2.0)  # Reduced timeout
          # Always show final success message
        print("✅ Bot shutdown complete")

    def on_stop_button_press(self, event):
        """Show stopping message when stop button is pressed down"""
        self.add_log("Stop button pressed - preparing to close...", "warning")
    
    def on_stop_button_release(self, event):
        """Execute stop and close when button is released"""
        if self.is_running:
            self.add_log("Stopping bot and closing application...", "warning")
            self.stop_bot()
            # Reduced wait time since we now wait for proper shutdown in stop_bot
            self.root.after(500, self.root.destroy)
        else:
            self.root.destroy()

    def stop_and_close(self):
        """Stop the bot and close the application - Legacy method"""
        if self.is_running:
            self.add_log("Stopping bot and closing application...", "warning")
            self.stop_bot()            # Reduced wait time since we now wait for proper shutdown in stop_bot
            self.root.after(500, self.root.destroy)
        else:
            self.root.destroy()
    
    def refresh_collection(self):
        """Refresh the Traktor collection by copying the latest file and reloading stats"""
        def _refresh():
            try:
                from config.settings import Settings
                from utils.traktor import refresh_collection_json
                
                # Check if original Traktor collection file exists
                if not Settings.TRAKTOR_PATH or not os.path.exists(Settings.TRAKTOR_PATH):
                    print("❌ Original Traktor collection file not found or not configured")
                    return
                
                print("🔄 Refreshing collection from Traktor...")
                print("📁 Converting XML to optimized JSON format...")
                  # Use the new JSON refresh workflow
                song_count = refresh_collection_json(
                    Settings.TRAKTOR_PATH, 
                    Settings.COLLECTION_JSON_FILE, 
                    Settings.EXCLUDED_ITEMS, 
                    debug_mode=True
                )
                
                print(f"✅ Collection refreshed successfully - {song_count} songs processed")
                  # Reset search counter on refresh
                self.search_count = 0
                # Reset the search counter file
                search_counter_file = Settings.SEARCH_COUNTER_FILE
                with open(search_counter_file, "w") as f:
                    f.write("0")
                self.root.after(0, lambda: self.searches_label.config(text=f"Song Searches: {self.search_count}"))
                print("🔄 Search counter reset")
                  # Now load the stats from the fresh JSON
                self.load_collection_stats()
                
            except Exception as e:
                error_msg = f"Error refreshing collection: {e}"
                print(f"❌ {error_msg}")
                
        # Run in background thread to avoid blocking UI
        threading.Thread(target=_refresh, daemon=True).start()
    
    def load_collection_stats(self):
        """Load and display collection statistics"""
        def _load_stats():
            try:
                # Import here to avoid circular imports
                from utils.traktor import load_collection_json, count_songs_in_collection_json, get_new_songs_json, refresh_collection_json
                from config.settings import Settings
                import os                # Check if JSON collection file exists, if not create it
                if not os.path.exists(Settings.COLLECTION_JSON_FILE):
                    print("⚠️ Collection JSON not found, creating from Traktor collection...")
                    if Settings.TRAKTOR_PATH and os.path.exists(Settings.TRAKTOR_PATH):
                        try:
                            print("📁 Converting XML to optimized JSON format...")
                            song_count = refresh_collection_json(
                                Settings.TRAKTOR_PATH, 
                                Settings.COLLECTION_JSON_FILE, 
                                Settings.EXCLUDED_ITEMS, 
                                debug_mode=True
                            )
                            print(f"✅ Initial collection import completed successfully - {song_count} songs processed")
                        except Exception as e:
                            print(f"❌ Error creating collection JSON: {e}")
                            self.root.after(0, lambda: self.songs_label.config(text="Songs: Error creating collection"))
                            self.root.after(0, lambda: self.new_songs_label.config(text="New Songs: Error creating collection"))
                            return
                    else:
                        print("❌ Traktor collection path not configured or file not found")
                        self.root.after(0, lambda: self.songs_label.config(text="Songs: Traktor path not found"))
                        self.root.after(0, lambda: self.new_songs_label.config(text="New Songs: Traktor path not found"))
                        return
                  # Load collection from JSON and show loading message
                print(f"📊 Loading collection stats from JSON: {Settings.COLLECTION_JSON_FILE}")
                songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
                
                if songs:
                    # Count total songs
                    total_songs = count_songs_in_collection_json(songs)
                    
                    # Count new songs (last 7 days)
                    _, new_songs_count = get_new_songs_json(songs, Settings.NEW_SONGS_DAYS, 1000)
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: self.songs_label.config(text=f"Songs: {total_songs:,}"))
                    self.root.after(0, lambda: self.new_songs_label.config(text=f"New Songs: {new_songs_count:,}"))
                      # Update import date
                    date_str, time_str = self.get_collection_import_date()
                    self.root.after(0, lambda: self.import_date_label.config(text=date_str))
                    self.root.after(0, lambda: self.import_time_label.config(text=time_str))
                    
                    # Update controls frame sizing after content changes
                    self.root.after(50, self.update_controls_frame_sizing)
                    
                    # Print results to both terminal and GUI
                    print(f"📊 Collection stats: {total_songs:,} total songs, {new_songs_count:,} new songs")
                else:
                    error_msg = "Collection JSON not found or empty"
                    print(f"⚠️  {error_msg}")
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
        
        # Load stats in background thread to avoid blocking UI
        threading.Thread(target=_load_stats, daemon=True).start()
    
    def clear_log(self):
        """Clear the output log"""
        self.output_text.delete("1.0", tk.END)
        self.add_log("Log cleared", "info")
    
    def clear_track_history(self):
        """Clear track history in NowPlaying config.json"""
        def _clear_history():
            try:
                from config.settings import Settings
                import json
                import shutil
                
                if not Settings.is_nowplaying_enabled():
                    print("❌ NowPlaying integration is not enabled")
                    return
                
                if not Settings.NOWPLAYING_CONFIG_JSON_PATH:
                    print("❌ Config file path not set in environment variable NOWPLAYING_CONFIG_JSON_PATH")
                    return

                print("🗑️ Clearing track history...")
                
                # Backup config.json
                backup_path = Settings.NOWPLAYING_CONFIG_JSON_PATH + ".bak"
                shutil.copyfile(Settings.NOWPLAYING_CONFIG_JSON_PATH, backup_path)
                print(f"📁 Backup saved as {backup_path}")

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
                    config["trackList"] = []                # Save updated config.json
                with open(Settings.NOWPLAYING_CONFIG_JSON_PATH, "w", encoding="utf-8") as file:
                    json.dump(config, file, indent=4)

                print("✅ Track history cleared successfully")
                
            except Exception as e:
                error_msg = f"Error clearing track history: {e}"
                print(f"❌ {error_msg}")        # Run in background thread to avoid blocking UI
        threading.Thread(target=_clear_history, daemon=True).start()

    def show_test_message(self):
        """Legacy method - no longer used but kept for compatibility"""
        pass

    def load_search_count(self):
        """Load the search count from file"""
        try:
            search_counter_file = "search_counter.txt"
            try:
                with open(search_counter_file, "r") as f:
                    self.search_count = int(f.read().strip())
            except (FileNotFoundError, ValueError):
                self.search_count = 0
        except Exception as e:
            print(f"Error loading search count: {e}")
            self.search_count = 0
    
    def update_search_count_display(self):
        """Update the search count display by reading from file"""
        try:
            search_counter_file = "search_counter.txt"
            try:
                with open(search_counter_file, "r") as f:
                    new_count = int(f.read().strip())
                if new_count != self.search_count:
                    self.search_count = new_count
                    self.searches_label.config(text=f"Song Searches: {self.search_count}")
            except (FileNotFoundError, ValueError):
                pass
        except Exception as e:
            print(f"Error updating search count display: {e}")
    
    def get_collection_import_date(self):
        """Get the modification date of the collection.json file"""
        try:
            from config.settings import Settings
            import os
            from datetime import datetime
            
            collection_file = Settings.COLLECTION_JSON_FILE
            if os.path.exists(collection_file):
                # Get file modification time
                mod_time = os.path.getmtime(collection_file)
                # Convert to readable format - separate date and time
                dt = datetime.fromtimestamp(mod_time)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M:%S")
                return date_str, time_str
            else:
                return "Not available", ""
        except Exception as e:
            print(f"Error getting collection import date: {e}")
            return "Error", ""
    
    def update_import_date_display(self):
        """Update the import date display"""
        try:
            date_str, time_str = self.get_collection_import_date()
            self.import_date_label.config(text=date_str)
            self.import_time_label.config(text=time_str)
        except Exception as e:
            print(f"Error updating import date display: {e}")
            self.import_date_label.config(text="Error")
            self.import_time_label.config(text="")
    
    def update_statistics(self):
        """Update statistics labels (songs, new songs, import date)"""
        self.load_collection_stats()
        self.update_import_date_display()
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            result = messagebox.askyesno(
                "Confirm Exit", 
                "The bot is still running. Do you want to stop it and exit?"
            )
            if result:
                print("🔄 User requested application close - stopping bot...")
                self.stop_bot()                # Reduced wait time since we now have proper shutdown
                self.root.after(500, self.root.destroy)
            return        
        
        print("🔄 Closing application...")
        self.root.destroy()
    
    def calculate_optimal_button_width(self, button_texts):
        """Calculate optimal button width based on the longest text"""
        max_length = 0
        for text in button_texts:            # Simple character count with some accommodation for emojis
            text_length = len(text)
            max_length = max(max_length, text_length)        # Minimal padding to prevent text cutoff while keeping buttons compact
        optimal_width = max_length  # No extra padding - just the text length
        return max(optimal_width, 12)  # Further reduced minimum from 16 to 12
    
    def calculate_controls_frame_width(self):
        """Calculate optimal width for controls frame based on content"""
        max_width = 0
        
        # Check button widths (this should be the controlling factor)
        button_texts = [
            "🛑 Stop & Close",
            "🗑️ Clear Log", 
            "🔄 Refresh Collection & Stats"
        ]
        if self.nowplaying_enabled:
            button_texts.append("🧹 Clear NP Track Info")
        
        button_width = self.calculate_optimal_button_width(button_texts)
        max_width = max(max_width, button_width)
        
        # Check typical stats content (be more conservative)
        stats_texts = [
            "Songs: 999,999",  # Reasonable max
            "New Songs: 9,999"
        ]
        
        for text in stats_texts:
            max_width = max(max_width, len(text))
          # Much more conservative padding
        return max_width + 2  # Minimal padding only
    
    def update_controls_frame_sizing(self):
        """Update controls frame sizing after content changes"""
        try:
            optimal_width = self.calculate_controls_frame_width()
            # Convert character width to approximate pixel width (more conservative)
            pixel_width = optimal_width * 7  # Reduced from 8 to 7 pixels per character
              # Set minimum size but allow expansion if needed
            controls_frame = self.stop_button.master  # Get the controls frame
            controls_frame.grid_columnconfigure(0, minsize=pixel_width)
            
        except Exception as e:
            print(f"Error updating controls frame sizing: {e}")
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

    def initialize_collection_on_startup(self):
        """Initialize collection by importing from .nml file (same as refresh)"""
        def _initialize():
            try:
                from config.settings import Settings
                from utils.traktor import refresh_collection_json, load_collection_json, count_songs_in_collection_json, get_new_songs_json
                
                # Always refresh from .nml file to ensure latest data and consistent messaging
                print("🔄 Importing collection from Traktor...")
                print("📁 Converting XML to optimized JSON format...")
                  # Use the same refresh workflow as the refresh button
                song_count = refresh_collection_json(
                    Settings.TRAKTOR_PATH, 
                    Settings.COLLECTION_JSON_FILE, 
                    Settings.EXCLUDED_ITEMS, 
                    debug_mode=True
                )
                
                print(f"✅ Collection imported successfully - {song_count} songs processed")
                
                # Load the collection and update stats
                songs = load_collection_json(Settings.COLLECTION_JSON_FILE)
                if songs:
                    total_songs = count_songs_in_collection_json(songs)
                    _, total_new_songs = get_new_songs_json(songs, Settings.NEW_SONGS_DAYS, Settings.MAX_SONGS, Settings.DEBUG)
                    print(f"📊 Collection stats: {total_songs:,} total songs, {total_new_songs:,} new songs")
                      # Update UI on main thread
                    self.root.after(0, lambda: self.songs_label.config(text=f"Songs: {total_songs:,}"))
                    self.root.after(0, lambda: self.new_songs_label.config(text=f"New Songs: {total_new_songs:,}"))
                    
                    # Update import date
                    date_str, time_str = self.get_collection_import_date()
                    self.root.after(0, lambda: self.import_date_label.config(text=date_str))
                    self.root.after(0, lambda: self.import_time_label.config(text=time_str))
                    
                    # Update controls frame sizing after content changes
                    self.root.after(50, self.update_controls_frame_sizing)
                else:
                    print("⚠️ Collection JSON is empty or could not be loaded")
                    self.root.after(0, lambda: self.songs_label.config(text="Songs: Collection not found"))
                    self.root.after(0, lambda: self.new_songs_label.config(text="New Songs: Collection not found"))
                    
            except Exception as e:
                error_msg = f"Error initializing collection: {e}"
                print(f"❌ {error_msg}")
                self.root.after(0, lambda: self.songs_label.config(text="Songs: Error loading"))
                self.root.after(0, lambda: self.new_songs_label.config(text="New Songs: Error loading"))
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=_initialize, daemon=True).start()
def main():
    """Main entry point for the GUI application"""
    # For PyInstaller executables, we don't need the directory check
    # since all modules are bundled inside the executable
    if not getattr(sys, 'frozen', False):
        # Only check directory when running as Python script
        if not os.path.exists('config/settings.py'):
            messagebox.showerror(
                "Setup Error",
                "This application must be run from the Traktor DJ NowPlaying Discord Bot directory.\n\n"
                "Please ensure you're in the correct directory and all required files are present."
            )
            return
    
    try:
        app = BotGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Application Error", f"Error starting GUI application: {e}")


if __name__ == "__main__":
    main()
