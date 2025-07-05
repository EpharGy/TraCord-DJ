"""
Configuration settings for TraCord DJ
Handles settings.json variables, constants, and validation
"""
import os
import json
from pathlib import Path
from typing import List, Optional
from utils.logger import debug, info, warning, error

# Path to settings.json (always in project root or config/data dir)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(USER_DATA_DIR, exist_ok=True)
SETTINGS_PATH = os.path.join(USER_DATA_DIR, 'settings.json')

class Settings:
    """Centralized configuration management loaded from settings.json"""
    _settings = {}

    @classmethod
    def load(cls):
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            cls._settings = json.load(f)
        # Set all keys as class attributes for easy reference
        for key, value in cls._settings.items():
            setattr(cls, key, value)

    @classmethod
    def get(cls, key, default=None):
        return cls._settings.get(key, default)

    @classmethod
    def reload(cls):
        cls.load()

    # File Paths
    @staticmethod
    def get_song_requests_file():
        return os.path.join(USER_DATA_DIR, 'song_requests.json')
    @staticmethod
    def get_stats_file():
        return os.path.join(USER_DATA_DIR, 'stats.json')
    @staticmethod
    def get_collection_json_file():
        return os.path.join(USER_DATA_DIR, 'collection.json')

    # Assign file paths after class definition
    SONG_REQUESTS_FILE: str = ""
    STATS_FILE: str = ""
    COLLECTION_JSON_FILE: str = ""

    # Processed Lists (populated in initialize)
    CHANNEL_IDS: List[int] = []
    ADMIN_IDS: List[int] = []
    DISCORD_LIVE_NOTIFICATION_ROLES: List[str] = []
    TRAKTOR_PATH: str = ""
    DEBUG: bool = False

    # Exclusion Patterns
    EXCLUDED_ITEMS = {
        'FILE': ['.stem.'],
        'DIR': [':ContentImport/', ':Samples/']
    }

    # Additional Settings
    TRAKTOR_BROADCAST_PORT: int = 0
    NEW_SONGS_DAYS: int = 0
    MAX_SONGS: int = 0
    TIMEOUT: float = 0.0
    CONSOLE_PANEL_WIDTH: int = 0
    COVER_SIZE: int = 0
    FADE_STYLE = "fade"  # Options: 'crossfade', 'fade' (fade to transparent then fade new image, double overall duration)
    FADE_FRAMES: int = 30
    FADE_DURATION: float = 1.0
    SPOUT_BORDER_PX: int = 0

    @classmethod
    def initialize(cls) -> None:
        cls.load()
        # Process ID lists
        channel_ids = cls.get('DISCORD_BOT_CHANNEL_IDS') or []
        admin_ids = cls.get('DISCORD_BOT_ADMIN_IDS') or []
        roles = cls.get('DISCORD_LIVE_NOTIFICATION_ROLES') or []
        cls.CHANNEL_IDS = [int(id) for id in channel_ids]
        cls.ADMIN_IDS = [int(id) for id in admin_ids]
        cls.DISCORD_LIVE_NOTIFICATION_ROLES = [str(role).strip() for role in roles]
        cls.DEBUG = bool(cls.get('DEBUG', False))
        # Import additional variables from settings.json
        def safe_int(val, default):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default
        def safe_float(val, default):
            try:
                return float(val)
            except (TypeError, ValueError):
                return default
        cls.TRAKTOR_BROADCAST_PORT = safe_int(cls.get('TRAKTOR_BROADCAST_PORT'), 8000)
        cls.NEW_SONGS_DAYS = safe_int(cls.get('NEW_SONGS_DAYS'), 7)
        cls.MAX_SONGS = safe_int(cls.get('MAX_SONGS'), 20)
        cls.TIMEOUT = safe_float(cls.get('TIMEOUT'), 45.0)
        cls.CONSOLE_PANEL_WIDTH = safe_int(cls.get('CONSOLE_PANEL_WIDTH'), 500)
        cls.COVER_SIZE = safe_int(cls.get('COVER_SIZE'), 150)
        cls.FADE_FRAMES = safe_int(cls.get('FADE_FRAMES'), 30)
        cls.FADE_DURATION = safe_float(cls.get('FADE_DURATION'), 1.0)
        cls.SPOUT_BORDER_PX = safe_int(cls.get('SPOUT_BORDER_PX'), 0)
        # Validate required settings
        required_vars = [
            cls.get('DISCORD_TOKEN'),
            cls.get('TRAKTOR_LOCATION'),
            cls.get('TRAKTOR_COLLECTION_FILENAME'),
            cls.get('DISCORD_BOT_APP_ID')
        ]
        if any(var is None for var in required_vars):
            raise ValueError("One or more required settings are missing in settings.json.")
        # Set up Traktor path
        cls._setup_traktor_path()

    @classmethod
    def _setup_traktor_path(cls) -> None:
        try:
            traktor_location = cls.get('TRAKTOR_LOCATION')
            traktor_collection_filename = cls.get('TRAKTOR_COLLECTION_FILENAME')
            if not traktor_location or not traktor_collection_filename:
                raise ValueError("TRAKTOR_LOCATION and TRAKTOR_COLLECTION_FILENAME must be set in settings.json.")
            from pathlib import Path
            traktor_dirs = [d for d in Path(traktor_location).iterdir() if d.is_dir() and d.name.startswith("Traktor ")]
            if not traktor_dirs:
                warning(f"No Traktor folders found in {traktor_location}. Please set the correct Traktor path in settings.")
                cls.TRAKTOR_PATH = ""
                return
            version_paths = []
            for path in traktor_dirs:
                version = path.name.replace("Traktor ", "").strip("\\")
                version_nums = [int(x) for x in version.split(".")]
                version_paths.append((version_nums, path))
            version_paths.sort(key=lambda x: x[0], reverse=True)
            latest_traktor_folder = str(version_paths[0][1])
            cls.TRAKTOR_PATH = os.path.join(latest_traktor_folder, traktor_collection_filename)
            if not os.path.exists(cls.TRAKTOR_PATH):
                warning(f"Collection file not found: {cls.TRAKTOR_PATH}. Please check your settings.")
                cls.TRAKTOR_PATH = ""
        except Exception as e:
            error(f"Error setting up Traktor path: {e}")
            cls.TRAKTOR_PATH = ""

# Assign file paths as class variables after class definition
Settings.SONG_REQUESTS_FILE = Settings.get_song_requests_file()
Settings.STATS_FILE = Settings.get_stats_file()
Settings.COLLECTION_JSON_FILE = Settings.get_collection_json_file()

# Initialize settings when module is imported
Settings.initialize()
