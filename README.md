# Traktor DJ NowPlaying Discord Bot

A comprehensive Discord bot for managing music requests, interacting with Traktor DJ software collections, and enhancing DJ workflow automation. This is a standalone GUI application suitable for personal DJ environments.

> **📝 Version & Releases**: Current version in [`version.py`](version.py) | Release history at [GitHub Releases](https://github.com/EpharGy/Traktor-DJ-NowPlaying-Discord-Bot/releases)

## Features

- **🖥️ Standalone GUI Application**: Tkinter-based control panel with real-time monitoring
- **🎵 Dynamic Song Search**: Intelligent search with interactive selection
- **📋 Song Request Management**: Full CRUD operations with user permissions
- **📂 Collection Management**: Automatic Traktor integration and collection refresh
- **🆕 New Song Tracking**: Display recently imported songs
- **📢 Live Streaming Notifications**: Broadcast notifications with role mentions
- **🔒 Permission System**: Granular access control for different user roles
- **🧹 Admin Controls**: Collection refresh and track history via GUI buttons
- **📊 Search Analytics**: Track and display search statistics
- **🎧 NowPlaying Integration**: (Optional) Clear recent playing history for seamless workflow - [NowPlaying App](https://www.nowplayingapp.com/)

## Quick Start

### 🎯 For End Users (No Python Required)

1. **Download** the latest `Traktor-DJ-NowPlaying-Discord-Bot-GUI.exe` from [Releases](https://github.com/your-repo/releases)
2. **Run** the executable - it will create a `.env` configuration file
3. **Edit** the `.env` file with your Discord bot token and settings
4. **Run** the executable again to start the bot

## Commands

### Music Discovery
- `/song <search>` - Search for songs with interactive selection (restricted to designated channels)
- `/srbnew [days]` - Display newly added songs from the last N days (default: 7)

### Request Management
- `/srbreqlist` - Display all pending song requests
- `/srbreqdel <number|'all'|'self'|username>` - Delete song requests with flexible options

### Utility Commands
- `/srblive <message>` - Send live streaming notifications with role mentions (admin only)

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
| `NOWPLAYING_CONFIG_JSON_PATH` | Path to the now playing configuration file (optional - leave blank if not using NowPlaying integration) |
| `SONG_REQUESTS_FILE` | Path to song requests JSON file (optional - defaults to song_requests.json in current directory) |

### 🛠️ For Developers

**Branches available:**
- `main` - Stable releases only
- `dev` - Active development (use this for contributions)

**Quick start:**
```bash
python gui.py  # Run the GUI application
```

## Running the Bot

### 🚀 GUI Application (Recommended)
- **Windows**: Double-click `start_bot.bat` or run the built executable
- **Cross-platform**: Run `python gui.py`

The GUI provides real-time monitoring, admin controls, and automatic bot startup.

### ⚡ Command Line (Advanced)
```bash
python main.py
```

## Building & Distribution

### 🏗️ Building for Distribution

Create a standalone executable for users without Python:

```bash
# Quick build (Windows)
build.bat

# Manual build
pip install -r requirements-dev.txt
python build.py
```

Output: `dist/Traktor-DJ-NowPlaying-Discord-Bot-GUI.exe`

### 📦 Distribution Notes
- Executable is fully portable and self-contained
- First run creates `.env` file with setup instructions
- No Python installation required for end users
- Can be run from any directory

## 🧩 Extending with Discord Cogs (Plugins)

This bot uses a dynamic cog loader! To add new features or commands, simply drop a `.py` file into the `cogs/` folder (if using EXE, create one where the exe is launched from). The bot will automatically load all cogs in this folder at startup—no need to edit the main code!

- **To add a new cog:**
  1. Place your `my_cool_feature.py` in the `cogs/` folder.
  2. Restart the bot. That's it! Your cog will be loaded automatically.
- **To remove a cog:**
  1. Delete or move the `.py` file from `cogs/`.
  2. Restart the bot.

## Project Structure

The bot uses a modular Discord.py Cogs architecture for better organization:

```
Traktor-DJ-NowPlaying-Discord-Bot/
├── 🚀 Entry Points
│   ├── gui.py                      # Main GUI application (recommended)
│   ├── main.py                     # Command-line entry point (dynamic cog loader)
│   ├── run_bot.py                  # Cross-platform launcher
│   └── start_bot.bat               # Windows batch launcher
├── 📁 Core Application
│   ├── cogs/                       # All bot features as plugins (just drop in .py files!)
│   │   ├── admin.py
│   │   ├── collection.py
│   │   ├── music.py
│   │   └── music_requests.py
│   ├── config/
│   │   └── settings.py
│   ├── gui/                        # GUI submodules (panels, controls, etc.)
│   │   ├── gui_controls_stats.py
│   │   ├── gui_logconsole.py
│   │   ├── gui_nowplaying.py
│   │   ├── gui_songrequests.py
│   │   └── __init__.py
│   ├── services/
│   │   └── discord_bot.py          # Discord bot lifecycle/controller logic
│   ├── utils/
│   │   ├── helpers.py              # Utility functions and permission checks
│   │   ├── logger.py               # Logging setup and output capture
│   │   ├── nowplaying.py           # NowPlaying integration helpers
│   │   └── traktor.py              # Traktor collection parsing and management
│   └── version.py                  # Version information
├── 🎨 Assets
│   ├── app_icon.ico
│   └── icon.png
├── 🔧 Build & Development
│   ├── .env.example
│   ├── build.bat
│   ├── build.py
│   ├── requirements-dev.txt
│   └── requirements.txt
├── 📖 Documentation
│   ├── LICENSE
│   ├── README.md
│   └── RELEASE.md
├── ⚙️ Configuration
│   ├── .gitignore
│   └── Traktor DJ NowPlaying Discord Bot.code-workspace
└── 📝 Generated Files (git-ignored)
    ├── .env
    ├── *.spec
    ├── build/
    ├── dist/
    ├── collection.json
    ├── collection.nml
    ├── search_counter.txt
    └── song_requests.json
```

> **Note:** The `gui/` folder contains all modular GUI panels and controls. The `services/` folder contains bot lifecycle logic. The `utils/` folder contains helpers, logging, and Traktor/NowPlaying utilities.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
