# TraCord DJ

A comprehensive Discord bot for managing music requests, interacting with Traktor DJ software collections, and enhancing DJ workflow automation. This is a standalone GUI application suitable for personal DJ environments. Spout integration is included for cover art display in other supported applications. Automatically creates a flask webserver for web overlays, allowing real-time song updates in OBS or other streaming software. MIDI support is included for song transitions, when enabled, a simple note is played when a song is played, allowing you to use this with other MIDI listeners. (recommend Free software for non-commercial, LoopBe1 - https://www.nerds.de/en/download.html)

> **📝 Version **: Current version in [`version.py`](version.py)

## Features

- **🖥️ Standalone GUI Application**: Tkinter-based control panel with real-time monitoring
- **🎧 Now Playing Song**: Traktor Broadcast Listening for Song/Artist details, integrated with collection details for advanced meta data (coverart, BPM, Key)
- **🖼️ Spout Cover Art Integration**: Send cover art to other applications via Spout (Windows only)
- **🖼️ Webpage for OBS/Overlays**: Flask webserver with Current Song Playing details. http://127.0.0.1:5000/
- **🖥️ MIDI**: Simple MIDI note played on song change (can use this to trigger things via MIDI)
- **🎵 Dynamic Song Search**: Intelligent search with interactive selection
- **📋 Song Request Management**: Full CRUD operations with user permissions
- **📂 Collection Integration**: Automatic Traktor collection integration for data
- **🆕 New Song Tracking**: Display recently imported songs
- **📢 Live Streaming Notifications**: Broadcast notifications with role mentions
- **🔒 Permission System**: Granular access control for different user roles or channels
- **🧹 Admin Controls**: Collection refresh and track history via GUI buttons
- **📊 Search Analytics**: Track and display search statistics

## Screenshots
# Main Interface
![TraCord DJ GUI](https://raw.githubusercontent.com/EpharGy/TraCord-DJ/main/assets/screenshots/gui_screenshot.png)

# Spout Cover Art Integration -> Nest Drop -> OBS
Any application that supports Spout can receive cover art from this bot, allowing you to display it in OBS or other software. (OBS does support spout directly via plugin)
![Spout Integration](https://raw.githubusercontent.com/EpharGy/TraCord-DJ/main/assets/screenshots/gui_spout_integration.png)

# Overlay Screenshots
Current workflow, Traktor -> TraCord DJ -> Spout/Web Overlay -> Nest Drop -> OBS
![Spout Integration](https://raw.githubusercontent.com/EpharGy/TraCord-DJ/main/assets/screenshots/overlay_coverart_1.png)
![Spout Integration](https://raw.githubusercontent.com/EpharGy/TraCord-DJ/main/assets/screenshots/overlay_coverart_2.png)
![Spout Integration](https://raw.githubusercontent.com/EpharGy/TraCord-DJ/main/assets/screenshots/overlay_coverart_3.png)

## Quick Start
**You must setup Various settings, settings.json will be created on first launch, these can then be set via the Settings button, Traktor path is the path with out the version folders, ie (C:/Users/{user}/Documents/Native Instruments/). Discord Token, ID's etc**
To Launch:
Python run_bot.py
Debug mode:
add --debug
Debug with no Discord connection:
add --debugd or --nodiscord


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

### Settings File
The bot uses a `settings.json` file for configuration. This file is created on the first run and can be edited via the GUI settings panel.

### Web Overlay
The web overlay can be found at http://127.0.0.1:5000/ you can use this in OBS, by default, width 1024px and height of 350px, this should be plenty in the case of text wrapping (entire panel has a default of 1024). By default cover art is 200px. Variables can be set at the top of the `default_overlay.html` file.

### 🛠️ For Developers

**Branches available:**
- `main` - Stable releases only
- `dev` - Active development (use this for contributions)

**Quick start:**
```bash
python run_bot.py  # Run the application
```

## Running the Bot

### 🚀 GUI Application (Recommended)
- **Windows**: Double-click `start_bot.bat` or run the built executable
- **Cross-platform**: Run `python run_bot.py`

The GUI provides real-time monitoring, admin controls, and automatic bot startup.

## 🧩 Extending with Discord Cogs (Plugins)

This bot uses a dynamic cog loader! To add new discord features or commands, simply drop a `.py` file into the `cogs/` folder (if using EXE, create one where the exe is launched from). The bot will automatically load all cogs in this folder at startup—no need to edit the main code!

- **To add a new cog:**
  1. Place your `my_cool_feature.py` in the `cogs/` folder.
  2. Restart the bot. That's it! Your cog will be loaded automatically.
- **To remove a cog:**
  1. Delete or move the `.py` file from `cogs/`.
  2. Restart the bot.

> **Note for Contributors:** The `_internal_cogs.py` file is auto-managed and contains an always-up-to-date list of internal cogs. Do not edit this file manually.

## Project Structure

The bot uses a modular Discord.py Cogs architecture for better organization:

```
TraCord-DJ/
├── 🚀 Entry Points
│   ├── debug_gui.py
│   ├── gui.py
│   ├── main.py
│   ├── run_bot.py
│   └── start_bot.bat
├── 📁 Core Application
│   ├── cogs/
│   │   ├── admin.py
│   │   ├── collection.py
│   │   ├── music.py
│   │   ├── music_requests.py
│   │   └── _internal_cogs.py
│   ├── config/
│   │   └── settings.py
│   ├── data/
│   │   ├── collection.json
│   │   ├── Debug_unmatched_songs.txt
│   │   ├── settings.json
│   │   ├── settings_example.json
│   │   ├── song_requests.json
│   │   ├── stats.json
│   │   └── _datafiles_stored_here.txt
│   ├── gui_components/
│   │   ├── gui_controls_stats.py
│   │   ├── gui_logconsole.py
│   │   ├── gui_now_playing.py
│   │   ├── gui_songrequests.py
│   │   ├── settings_dialog.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── discord_bot.py
│   │   ├── traktor_listener.py
│   │   └── web_overlay.py
│   ├── utils/
│   │   ├── events.py
│   │   ├── harmonic_keys.py
│   │   ├── helpers.py
│   │   ├── logger.py
│   │   ├── midi_helper.py
│   │   ├── song_matcher.py
│   │   ├── spout_sender_helper.py
│   │   ├── stats.py
│   │   └── traktor.py
│   ├── version.py
├── assets/
│   ├── app_icon.ico
│   ├── icon.png
│   └── screenshots/
│       ├── gui_screenshot.png
│       └── gui_spout_integration.png
├── web_overlay/
│   ├── templates/
│   │   └── default_overlay.html
├── requirements.txt
├── LICENSE
├── README.md
├── TODO-Main.md
└── TraCord DJ.code-workspace
```

> **Note:** The `gui_components/` folder contains all modular GUI panels and controls. The `services/` folder contains bot lifecycle logic. The `utils/` folder contains helpers, logging, and Traktor, Now Playing utilities. The `data/` and `extra_cogs/` folders are gitignored and not included in distributed builds.

## ⚙️ Discord Cog Loading Behavior

- All cogs in `cogs/` are always loaded and are considered part of the core bot functionality.
- Any `.py` files in `extra_cogs/` (top-level only) are also loaded as cogs.
- Errors for missing cogs in `extra_cogs` are suppressed for a clean dev experience.
- Use `extra_cogs/` for personal, experimental, or private cogs and files. This folder is gitignored by default. Create the folder if it does not exist.

## 🖼️ Spout Cover Art Integration (Optional)

This app supports sending cover art to other applications via Spout (Windows only) using [Python-SpoutGL](https://github.com/jlai/Python-SpoutGL).

- **Spout is optional**: The rest of the app works even if you do not install SpoutGL.
- If you click the Spout button in the GUI without SpoutGL installed, you will see a warning message.

### To enable Spout support:
1. Install dependencies:
   ```bash
   pip install PyOpenGL glfw
   ```
2. Clone and install Python-SpoutGL:
   ```bash
   git clone https://github.com/jlai/Python-SpoutGL.git
   cd Python-SpoutGL
   pip install .
   ```

**Do not include the Python-SpoutGL source in your own repo.** Just document these steps for users who want Spout support.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

