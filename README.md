# DJ Discord Bot

A comprehensive Discord bot for managing music requests, interacting with Traktor DJ software collections, and enhancing DJ workflow automation. **Version 1.0** introduces a complete standalone GUI application for ### 🎉 What's New in V1.0 - Complete Rewrite from V0.13:

**🏗️ ARCHITECTURAL TRANSFORMATION:**
- **Complete rewrite**: Single-file `SongBot.py` → Modular Discord.py Cogs system
- **New project structure**: Organized into `config/`, `utils/`, `cogs/` modules
- **Centralized configuration**: Environment handling in `config/settings.py`
- **Modular commands**: Music, collection, admin, and request management in separate cogs

**🖥️ BRAND NEW GUI APPLICATION:**
- **Standalone GUI**: Complete tkinter-based control panel replacing command-line interface
- **Auto-Start Bot**: Streamlined experience - bot starts automatically with GUI launch
- **Real-Time Dashboard**: Live bot status, logs, collection statistics, and search counter
- **GUI Admin Controls**: Collection refresh and track history management via intuitive buttons
- **Dynamic Interface**: Auto-sizing UI elements for optimal display across different content

**🛠️ ROBUST DISTRIBUTION SYSTEM:**
- **PyInstaller Integration**: Build standalone executables with `build.py` and `build.bat`
- **Portable Executable**: Runs from any directory, resolves all file paths correctly
- **Auto-Setup System**: Creates `.env` from template on first run with user guidance
- **Template Detection**: Warns users about unconfigured template values
- **Two-Step Setup**: Create config file, then launch - seamless first-time experience

**🧹 MODERNIZATION & CLEANUP:**
- **Removed Admin Commands**: `/srbtraktorrefresh` and `/srbnpclear` moved to GUI buttons
- **Enhanced Error Handling**: Robust PyInstaller compatibility and null safety
- **Smart File Management**: All data files auto-created and managed relative to executable
- **Professional Output**: Clean logging with color coding and timestamp display
- **Fast Shutdown**: Instant Discord disconnect with proper cleanup

**📦 PRODUCTION FEATURES:**
- **Versioned Builds**: Executable naming includes version (DJ-Discord-Bot-GUI-v1.0.0.exe)
- **Complete Documentation**: Separate guides for end users vs developers
- **Cross-Platform**: Works in both development and compiled executable modes
- **Professional Grade**: Desktop application suitable for live DJ environmentsments.

## 🎯 Version 1.0 Highlights

**GUI-First Experience**: This major release transforms the bot from a command-line tool into a desktop application. All admin functions have been moved from Discord commands to an intuitive GUI interface, providing better workflow integration for live DJ environments.

## Features

- **Standalone GUI Application**: Tkinter-based control panel with real-time log monitoring and statistics
- **Dynamic Song Search**: Search for songs with intelligent prioritization and interactive selection
- **Song Request Management**: Full CRUD operations for song requests with user permissions
- **Collection Management**: Automatic Traktor version detection and collection refresh through GUI
- **New Song Tracking**: Display recently imported songs with configurable date ranges
- **Live Streaming Notifications**: Broadcast live notifications with role mentions
- **Permission System**: Granular access control for different user roles
- **Track History Management**: Clear track history through GUI interface
- **Smart Filtering**: Configurable exclusion of stem files and content imports
- **Interactive Interface**: Timeout-based user interactions with numbered selections
- **Search Counter**: Track the number of song searches performed since startup

## Setup

### For End Users (Standalone Executable)

🎯 **Quick Start - No Python Required:**

1. **Download** the latest `DJ-Discord-Bot-GUI-v*.exe` from the [Releases](https://github.com/your-repo/releases) page
2. **Run** the executable - it will automatically create a `.env` configuration file
3. **Configure** the `.env` file with your settings (see popup message for details)
4. **Relaunch** the executable to start using the bot

📝 **First-time setup process:**
- When you first run the executable, you'll see a setup dialog explaining that a `.env` file has been created
- Edit the `.env` file with your Discord bot token, channel IDs, and file paths
- The application will validate your configuration on the next launch

### For Developers (Source Code)

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Traktor DJ Software

### Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd DJ-Discord-Bot
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the GUI application** - it will create a `.env` template:
   ```bash
   python gui.py
   ```

4. **Configure the auto-created `.env` file** with your actual values:
   ```env
   DISCORD_TOKEN=your_discord_bot_token
   APPLICATION_ID=your_application_id
   CHANNEL_IDS=channel_id_1,channel_id_2
   ALLOWED_USER_IDS=user_id_1,user_id_2
   DISCORD_LIVE_NOTIFICATION_ROLES=Tunes,DJ Friends,Music Lovers
   TRAKTOR_LOCATION=path_to_traktor_folder
   TRAKTOR_COLLECTION_FILENAME=collection.nml
   NOWPLAYING_CONFIG_JSON_PATH=path_to_nowplaying_config
   SONG_REQUESTS_FILE=song_requests.json
   ```

## Running the Bot

### Standalone GUI Application (Recommended)
For the best user experience, use the standalone GUI application:

**🚀 First-Time Users (Executable):**
1. **First Launch**: Run the executable - it creates a `.env` file and shows setup instructions
2. **Configure**: Edit the `.env` file with your Discord bot settings and file paths
3. **Second Launch**: Run the executable again to start the bot

**🛠️ Developers (Source Code):**
- **Windows**: Double-click `start_bot.bat` or run `python run_bot.py`
- **Cross-platform**: Run `python gui.py`

The GUI provides:
- ✅ **Automatic Bot Startup** - No manual start required, bot launches with GUI (after configuration)
- ✅ **Real-Time Monitoring** - Live bot status, logs, and error tracking
- ✅ **Collection Statistics** - Song count, new songs, and search counter
- ✅ **Admin Controls** - Refresh collection and clear NP track info via buttons
- ✅ **Dynamic Interface** - Auto-sizing buttons and panels for optimal display
- ✅ **Fast Shutdown** - Immediate Discord offline status when closing
- ✅ **Improved Design** - Clean, intuitive interface for DJ workflow

### Command Line (Advanced)
For development or server deployment:
```bash
python main.py
```

## Building & Distribution

### For Developers with Python
Simply run the GUI application directly:
```bash
python gui.py
```

### Building for Distribution

For distribution to users who don't have Python installed, build a standalone executable:

#### Quick Build (Windows)
```bash
# Double-click build.bat, or run:
build.bat
```

#### Manual Build Process
```bash
# Install build dependencies
pip install -r requirements-dev.txt

# Build GUI executable (no console window)
python build.py
```

#### Build Output
This creates a versioned executable in the `dist/` folder:
- **DJ-Discord-Bot-GUI-v1.0.0.exe** - Ready for distribution

### GitHub Releases Management

#### For Repository Maintainers:
1. **Build the executable**:
   ```bash
   python build.py
   ```

2. **Test the executable** on a clean system (without Python):
   - Test without `.env` file (should auto-create and show setup dialog)
   - Test with template values (should warn about configuration)
   - Test with proper configuration (should run normally)

3. **Create a GitHub Release**:
   - Go to GitHub → Releases → "Create a new release"
   - Tag version (e.g., `v1.0.0`)
   - Upload `DJ-Discord-Bot-GUI-v1.0.0.exe` from the `dist/` folder
   - Include release notes

#### For End Users:
- **With Python**: Clone the repo and run `python gui.py`
- **Without Python**: Download the `.exe` file from GitHub Releases

### Distribution Notes
- **The executable is fully portable and self-contained**
- **Automatic setup**: First run creates `.env` file with template and instructions
- **Two-step process**: Configure `.env` after first run, then relaunch
- **The executable will look for files (like `.env`) in its own directory**
- **Can be run from anywhere** - files are created in the executable's directory
- **No Python installation required** for end users
- **Traktor collection file path** should be specified with full absolute path in `.env`

### Example Setup for End Users:
```
MyBot/
├── DJ-Discord-Bot-GUI-v1.0.0.exe
├── .env                    (auto-created on first run, configure manually)
└── song_requests.json      (created automatically)
```

## Project Structure

The bot uses a modular Discord.py Cogs architecture for better organization:

```
DJ-Discord-Bot/
├── 🚀 Launchers
│   ├── gui.py              # Standalone GUI application
│   ├── run_bot.py          # Cross-platform launcher
│   ├── start_bot.bat       # Windows batch launcher
│   └── main.py             # Command-line entry point
├── 📁 Core Application
│   ├── config/
│   │   └── settings.py     # Environment variables and configuration
│   ├── utils/
│   │   ├── traktor.py      # Traktor collection parsing and management
│   │   └── helpers.py      # Utility functions and permission checks
│   └── cogs/
│       ├── music.py        # Music search and song request commands
│       ├── collection.py   # Collection management commands
│       ├── requests.py     # Song request list management
│       └── admin.py        # Administrative commands
├── 📄 Configuration
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
└── 📖 Documentation
    ├── README.md
    └── LICENSE
```

## Commands

### Music Discovery
- `/song <search>` - Search for songs with interactive selection (restricted to designated channels)
- `/srbnew [days]` - Display newly added songs from the last N days (default: 7)

### Request Management
- `/srbreqlist` - Display all pending song requests
- `/srbreqdel <number|'all'|'self'|username>` - Delete song requests with flexible options

### Utility Commands
- `/srblive <message>` - Send live streaming notifications with role mentions (admin only)

> **Note**: Admin commands `/srbtraktorrefresh` and `/srbnpclear` have been removed from Discord and are now available as GUI buttons for better workflow integration.

## Version History

**Versioning Scheme**: We follow **Semantic Versioning (SemVer)** `vA.B.C` where:
- **A (Major)**: Major rewrites, breaking changes, architectural overhauls
- **B (Minor)**: New features, enhancements, backwards-compatible additions
- **C (Patch)**: Bug fixes, maintenance updates, minor improvements

### Release Timeline:
📍 **V0.1**: Basic search functionality  
🛡️ **V0.6**: Production-ready with robust error handling  
🎵 **V0.9**: Interactive request system with full reorganization  
📢 **V0.11**: Community features with live notifications  
🔄 **V0.12**: Dynamic version management and future-proofing  
✨ **V0.13**: Code quality improvements - eliminated all lint/type errors, enhanced null safety  
🎯 **V1.0.0**: **MAJOR RELEASE** - Complete rewrite with standalone GUI application

### 🎉 What's New in V1.0:
- 🖥️ **Standalone GUI Application**: Complete tkinter-based control panel replacing command-line interface
- 🚀 **Auto-Start Bot**: Streamlined experience - bot starts automatically with GUI launch
- 📊 **Real-Time Dashboard**: Live bot status, logs, collection statistics, and search counter
- � **GUI Admin Controls**: Collection refresh and track history management via intuitive buttons
- 🧹 **Simplified Discord**: Removed redundant admin commands - all admin functions now in GUI
- 📈 **Smart Analytics**: Search counter with auto-reset, new song tracking, collection stats
- ⚡ **Fast Operations**: Instant Discord disconnect, optimized shutdown process
- 🎨 **Dynamic Interface**: Auto-sizing UI elements for optimal display across different content
- 🏆 **Production Ready**: Desktop application suitable for live DJ environments

*Full version history available in git commits with detailed changelogs*

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Your Discord bot token |
| `APPLICATION_ID` | Your Discord application ID |
| `CHANNEL_IDS` | Comma-separated list of channel IDs where the bot can be used |
| `ALLOWED_USER_IDS` | Comma-separated list of user IDs allowed to use admin commands |
| `DISCORD_LIVE_NOTIFICATION_ROLES` | Comma-separated list of role names to mention for live notifications (optional) |
| `TRAKTOR_LOCATION` | Path to your Traktor installation folder |
| `TRAKTOR_COLLECTION_FILENAME` | Name of the Traktor collection file |
| `NOWPLAYING_CONFIG_JSON_PATH` | Path to the now playing configuration file |
| `SONG_REQUESTS_FILE` | Path to song requests JSON file (optional - defaults to song_requests.json in current directory) |

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
