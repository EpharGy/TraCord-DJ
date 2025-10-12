"""Legacy-friendly logging wrapper backed by the stdlib logging module."""
from __future__ import annotations

import logging
from threading import Lock
from typing import Any, Optional


class BotLogger:
    """Centralized logger with optional GUI callbacks."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    _instance: Optional["BotLogger"] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self._gui_callback = None
        self._debug_enabled = False
        self._level = self.INFO
        self._logger = logging.getLogger("tracord")
        self._logger.setLevel(self._level)
        self._logger.propagate = True

    def set_debug_mode(self, enabled: bool):
        """Programmatically enable or disable debug mode"""
        self._debug_enabled = enabled
        self._level = self.DEBUG if enabled else self.INFO
        self._logger.setLevel(self._level)
    
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
        else:
            level_prefix = "[UNKNOWN] "  # Fallback for unknown levels
        
        if self._debug_enabled:
            # In debug mode, show both [DEBUG] and level prefixes
            debug_prefix = "[DEBUG] " if level != self.DEBUG else ""
            return f"{debug_prefix}{level_prefix}{message}"
        else:
            # In normal mode, show level prefixes for all levels
            return f"{level_prefix}{message}"
    
    def _log(self, message: str, level: int):
        """Internal logging method"""
        if not self._should_log(level):
            return

        formatted_message = self._format_message(message, level)

        # Send to stdlib logging
        self._logger.log(level, formatted_message)

        # Also send to GUI if callback is set
        if self._gui_callback:
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


class OutputCapture:
    """
    Captures output from stdout/stderr and routes it to both the original stream and a queue or callback (e.g., for GUI log panel).
    """
    def __init__(self, queue_obj, tag, original, gui_instance=None):
        self.queue = queue_obj
        self.tag = tag
        self.original = original
        self.gui = gui_instance

    def write(self, text):
        # Always write to original first (terminal)
        self.original.write(text)
        self.original.flush()
        # Then capture for GUI (only non-empty lines)
        if text.strip():
            self.queue.put((self.tag, text.strip()))

    def flush(self):
        self.original.flush()


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
