# Traktor DJ NowPlaying Discord Bot

A comprehensive Discord bot for managing music requests, interacting with Traktor DJ software collections, and enhancing DJ workflow automation. This is a standalone GUI application suitable for personal DJ environments.

> **📝 Version & Changelog**: Current version and complete changelog available in [`version.py`](version.py)

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

### 🛠️ For Developers

1. **Clone** the repository and install dependencies:
   ```bash   git clone <your-repo-url>
   cd Traktor-DJ-NowPlaying-Discord-Bot
   pip install -r requirements.txt
   ```

2. **Run** the GUI application:
   ```bash
   python gui.py
   ```

3. **Configure** the auto-created `.env` file and relaunch

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

## Project Structure

The bot uses a modular Discord.py Cogs architecture for better organization:

```
Traktor-DJ-NowPlaying-Discord-Bot/
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
│   ├── version.py          # Version and changelog information
│   └── .gitignore
└── 📖 Documentation
    ├── README.md
    └── LICENSE
```

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
