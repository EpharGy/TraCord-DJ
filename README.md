# DJ Discord Bot

A Discord bot for managing music requests and interacting with Traktor DJ software collections.

## Features

- **Song Search**: Search for songs in your Traktor collection
- **Collection Refresh**: Update the Traktor collection file
- **Permission System**: Restrict commands to specific users and channels
- **Environment Configuration**: Secure token and configuration management

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

- `/srbcol` - Refresh the Traktor collection file (restricted to allowed users)
- `/song <search>` - Search for a song in the Traktor collection (restricted to designated channels)

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Your Discord bot token |
| `APPLICATION_ID` | Your Discord application ID |
| `CHANNEL_IDS` | Comma-separated list of channel IDs where the bot can be used |
| `ALLOWED_USER_IDS` | Comma-separated list of user IDs allowed to use admin commands |
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
