# DJ Discord Bot

A comprehensive Discord bot for managing music requests, interacting with Traktor DJ software collections, and enhancing DJ workflow automation.

## Features

- **Dynamic Song Search**: Search for songs with intelligent prioritization and interactive selection
- **Song Request Management**: Full CRUD operations for song requests with user permissions
- **Collection Management**: Automatic Traktor version detection and collection refresh
- **New Song Tracking**: Display recently imported songs with configurable date ranges
- **NowPlaying Integration**: Clear track history and manage NowPlaying configurations
- **Live Streaming Notifications**: Broadcast live notifications with role mentions
- **Permission System**: Granular access control for different user roles
- **Smart Filtering**: Configurable exclusion of stem files and content imports
- **Interactive Interface**: Timeout-based user interactions with numbered selections

## Setup

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

3. Create a `.env` file in the project root with the following variables:
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

4. Run the bot:
   ```bash
   python SongBot.py
   ```

## Commands

### Music Discovery
- `/song <search>` - Search for songs with interactive selection (restricted to designated channels)
- `/srbnew [days]` - Display newly added songs from the last N days (default: 7)

### Collection Management  
- `/srbtraktorrefresh` - Refresh the Traktor collection file (admin only)

### Request Management
- `/srbreqlist` - Display all pending song requests
- `/srbreqdel <number|'all'|'self'|username>` - Delete song requests with flexible options

### Utility Commands
- `/srbnpclear` - Backup and clear NowPlaying track history (admin only)
- `/srblive <message>` - Send live streaming notifications with role mentions (admin only)

## Version History

📍 **V0.1**: Basic search functionality  
🛡️ **V0.6**: Production-ready with robust error handling  
🎵 **V0.9**: Interactive request system with full reorganization  
📢 **V0.11**: Community features with live notifications  
🔄 **V0.12**: Dynamic version management and future-proofing  
✨ **V0.13**: Code quality improvements - eliminated all lint/type errors, enhanced null safety

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
| `SONG_REQUESTS_FILE` | Name of the song requests JSON file |

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
