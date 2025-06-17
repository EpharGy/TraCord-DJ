"""
Centralized logging system for Traktor DJ NowPlaying Discord Bot
Provides consistent logging to both terminal and GUI with configurable debug levels
"""
import os
import sys
from datetime import datetime
from typing import Optional, Any
from threading import Lock


class BotLogger:
    """
    Centralized logger that outputs to both terminal and GUI
    Supports different log levels and debug mode configuration
    """
    
    # Log levels
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one logger instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger with default settings"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._gui_callback = None
        self._debug_enabled = False
        self._level = self.INFO
        
        # Check for debug mode from environment or will be set programmatically
        self._check_debug_mode()
    
    def _check_debug_mode(self):
        """Check if debug mode should be enabled"""
        # Check environment variable
        debug_env = os.getenv('TRAKTOR_DEBUG', '').lower()
        if debug_env in ['true', '1', 'yes', 'on']:
            self._debug_enabled = True
            self._level = self.DEBUG
        
        # Check command line arguments
        if '--debug' in sys.argv:
            self._debug_enabled = True
            self._level = self.DEBUG
    
    def set_debug_mode(self, enabled: bool):
        """Programmatically enable or disable debug mode"""
        self._debug_enabled = enabled
        self._level = self.DEBUG if enabled else self.INFO
    
    def set_gui_callback(self, callback):
        """Set the GUI callback function for displaying messages in GUI"""
        self._gui_callback = callback
    
    def _should_log(self, level: int) -> bool:
        """Check if message should be logged based on current level"""
        return level >= self._level
    
    def _format_message(self, message: str, level: int) -> str:
        """Format message based on debug mode and level"""
        # First determine the level prefix
        level_prefix = ""
        if level == self.DEBUG:
            level_prefix = "[DEBUG] "
        elif level == self.INFO:
            level_prefix = "[INFO] "
        elif level == self.WARNING:
            level_prefix = "[WARNING] "
        elif level == self.ERROR:
            level_prefix = "[ERROR] "
        
        if self._debug_enabled:
            # In debug mode, show both [DEBUG] and level prefixes
            debug_prefix = "[DEBUG] " if level != self.DEBUG else ""
            return f"{debug_prefix}{level_prefix}{message}"
        else:
            # In normal mode, only show level prefixes (but not [INFO] to keep it clean)
            if level == self.INFO:
                return message  # Clean INFO messages in normal mode
            else:
                return f"{level_prefix}{message}"
    
    def _log(self, message: str, level: int):
        """Internal logging method"""
        if not self._should_log(level):
            return
        
        formatted_message = self._format_message(message, level)
        
        # Always output to terminal
        print(formatted_message)
        
        # Also send to GUI if callback is set
        if self._gui_callback:
            # Determine GUI log level based on message content and level
            if level == self.ERROR:
                gui_level = "error"
            elif level == self.WARNING:
                gui_level = "warning"
            elif level == self.INFO and any(indicator in message for indicator in ["✅", "🟢", "ready", "success", "complete"]):
                gui_level = "success"
            else:
                gui_level = "info"
            
            try:
                self._gui_callback(formatted_message, gui_level)
            except Exception:
                # Don't let GUI callback failures break logging
                pass
    
    def debug(self, message: str):
        """Log a debug message (only shown in debug mode)"""
        self._log(message, self.DEBUG)
    
    def info(self, message: str):
        """Log an info message (always shown)"""
        self._log(message, self.INFO)
    
    def warning(self, message: str):
        """Log a warning message (always shown)"""
        self._log(message, self.WARNING)
    
    def error(self, message: str):
        """Log an error message (always shown)"""
        self._log(message, self.ERROR)
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is currently enabled"""
        return self._debug_enabled


# Create the global logger instance
logger = BotLogger()

# Convenience functions for easy importing
def debug(message: str):
    """Log a debug message"""
    logger.debug(message)

def info(message: str):
    """Log an info message"""
    logger.info(message)

def warning(message: str):
    """Log a warning message"""
    logger.warning(message)

def error(message: str):
    """Log an error message"""
    logger.error(message)

def set_debug_mode(enabled: bool):
    """Enable or disable debug mode"""
    logger.set_debug_mode(enabled)

def set_gui_callback(callback):
    """Set GUI callback for displaying messages"""
    logger.set_gui_callback(callback)

def is_debug_enabled() -> bool:
    """Check if debug mode is enabled"""
    return logger.is_debug_enabled()
