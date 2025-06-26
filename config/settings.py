"""
Configuration settings for TraCord DJ
Handles environment variables, constants, and validation
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional
from utils.logger import debug, info, warning, error

def get_executable_dir():
    """Get the directory where the executable or script is running from"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        return os.path.dirname(os.path.abspath(__file__))

# Load environment variables from the script/executable directory
env_path = os.path.join(get_executable_dir(), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

class Settings:
    """Centralized configuration management"""
    
    # Discord Configuration
    TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
    APPLICATION_ID: Optional[str] = os.getenv('APPLICATION_ID')
    
    # Channel and User Permissions
    CHANNEL_IDS_ENV: Optional[str] = os.getenv('CHANNEL_IDS')
    ALLOWED_USER_IDS_ENV: Optional[str] = os.getenv('ALLOWED_USER_IDS')
      # Traktor Configuration
    TRAKTOR_LOCATION: Optional[str] = os.getenv('TRAKTOR_LOCATION')
    TRAKTOR_COLLECTION_FILENAME: Optional[str] = os.getenv('TRAKTOR_COLLECTION_FILENAME')
    
    # File Paths - Use executable directory for file paths when frozen
    @staticmethod
    def get_song_requests_file():
        """Get the song requests file path, always in config directory."""
        base_dir = get_executable_dir()
        return os.path.join(base_dir, 'song_requests.json')
    
    @staticmethod
    def get_stats_file():
        """Get the stats file path, always in config directory."""
        base_dir = get_executable_dir()
        return os.path.join(base_dir, 'stats.json')
    
    
    @staticmethod
    def get_collection_json_file():
        """Get the collection JSON file path, handling both development and executable modes"""
        base_dir = get_executable_dir()
        return os.path.join(base_dir, 'collection.json')
    
    SONG_REQUESTS_FILE: str = get_song_requests_file()
    STATS_FILE: str = get_stats_file()
    COLLECTION_JSON_FILE: str = get_collection_json_file()
    
    # Live Notification Roles
    DISCORD_LIVE_NOTIFICATION_ROLES_ENV: Optional[str] = os.getenv('DISCORD_LIVE_NOTIFICATION_ROLES')
    
    # Processed Lists
    CHANNEL_IDS: List[int] = []
    ALLOWED_USER_IDS: List[int] = []
    DISCORD_LIVE_NOTIFICATION_ROLES: List[str] = []
    TRAKTOR_PATH: str = ""
    DEBUG: bool = False
    # Bot Constants
    NEW_SONGS_DAYS: int = int(os.getenv('NEW_SONGS_DAYS', 7))
    MAX_SONGS: int = int(os.getenv('MAX_SONGS', 20))
    TIMEOUT: float = float(os.getenv('TIMEOUT', 45.0))
    DEBUG: bool = False
    # Exclusion Patterns
    EXCLUDED_ITEMS = {
        'FILE': ['.stem.'],
        'DIR': [':ContentImport/', ':Samples/']
    }
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize and validate all settings"""
        # Process ID lists
        cls.CHANNEL_IDS = [int(id) for id in cls.CHANNEL_IDS_ENV.split(',')] if cls.CHANNEL_IDS_ENV else []
        cls.ALLOWED_USER_IDS = [int(id) for id in cls.ALLOWED_USER_IDS_ENV.split(',')] if cls.ALLOWED_USER_IDS_ENV else []
        
        # Process role list
        cls.DISCORD_LIVE_NOTIFICATION_ROLES = [
            role.strip() for role in cls.DISCORD_LIVE_NOTIFICATION_ROLES_ENV.split(',')
        ] if cls.DISCORD_LIVE_NOTIFICATION_ROLES_ENV else []
        
        # Validate required environment variables
        required_vars = [
            cls.TOKEN, cls.TRAKTOR_LOCATION, cls.TRAKTOR_COLLECTION_FILENAME, 
            cls.APPLICATION_ID
        ]        
        if any(var is None for var in required_vars):
            raise ValueError("One or more required environment variables are missing.")
        
        # Set up Traktor path
        cls._setup_traktor_path()
    
    @classmethod
    def _setup_traktor_path(cls) -> None:
        """Set up the Traktor collection file path with version detection"""
        try:
            if not cls.TRAKTOR_LOCATION or not cls.TRAKTOR_COLLECTION_FILENAME:
                raise ValueError("TRAKTOR_LOCATION and TRAKTOR_COLLECTION_FILENAME must be set")
            
            # Import here to avoid circular imports
            from pathlib import Path
            
            # Inline implementation of get_latest_traktor_folder to avoid circular imports
            try:
                # Get all directories that start with "Traktor "
                traktor_dirs = [d for d in Path(cls.TRAKTOR_LOCATION).iterdir() 
                               if d.is_dir() and d.name.startswith("Traktor ")]
                
                if not traktor_dirs:
                    raise ValueError(f"No Traktor folders found in {cls.TRAKTOR_LOCATION}")
                    
                # Extract version numbers and pair them with paths
                version_paths = []
                for path in traktor_dirs:
                    # Extract version number from folder name (e.g., "Traktor 4.2.0" -> "4.2.0")
                    version = path.name.replace("Traktor ", "").strip("\\")
                    # Split version into numeric components
                    version_nums = [int(x) for x in version.split(".")]
                    version_paths.append((version_nums, path))
                    
                # Sort by version numbers (newest first)
                version_paths.sort(key=lambda x: x[0], reverse=True)
                
                # Get the path of the newest version
                latest_traktor_folder = str(version_paths[0][1])
                
                cls.TRAKTOR_VERSION_FOLDER = os.path.basename(latest_traktor_folder)
                
            except Exception as e:
                raise ValueError(f"Error finding latest Traktor folder: {e}")
            
            cls.TRAKTOR_PATH = os.path.join(latest_traktor_folder, cls.TRAKTOR_COLLECTION_FILENAME)
            
            if not os.path.exists(cls.TRAKTOR_PATH):
                raise ValueError(f"Collection file not found: {cls.TRAKTOR_PATH}")
                
        except Exception as e:
            error(f"Error setting up Traktor path: {e}")
            raise

# Initialize settings when module is imported
Settings.initialize()
