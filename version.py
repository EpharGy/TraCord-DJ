"""
Version and Changelog for DJ Discord Bot

This file contains the current version and complete changelog.
For the latest version information, check this file or the GUI application.
"""

__version__ = "1.0.1"
__version_info__ = (1, 0, 1)

# =============================================================================
# VERSIONING SCHEME
# =============================================================================
# We follow Semantic Versioning (SemVer) vA.B.C:
# - A (Major): Major rewrites, breaking changes, architectural overhauls
# - B (Minor): New features, enhancements, backwards-compatible additions  
# - C (Patch): Bug fixes, maintenance updates, minor improvements

# =============================================================================
# COMPLETE CHANGELOG (Newest First)
# =============================================================================

# -----------------------------------------------------------------------------
# Version 1.0.1 - PATCH RELEASE (2025-06-15)
# -----------------------------------------------------------------------------
# Bug fixes and command cleanup
# 
# FIXES:
# - Fixed Discord command count display (now shows 5 commands instead of 7)
# - Fully removed Discord admin commands: /srbtraktorrefresh, /srbnpclear
# - Admin functions now available exclusively through GUI buttons
# - Added search_counter.txt to .gitignore (auto-created file)
# - Recovered all missing project files for complete build system
# - Updated documentation with changelog ordering (newest first)
# - Updated executable naming to static "DJ-Discord-Bot-GUI.exe"

# -----------------------------------------------------------------------------  
# Version 1.0.0 - MAJOR RELEASE (2025-06-15)
# -----------------------------------------------------------------------------
# Complete rewrite from V0.13 single-file bot to modular GUI application
#
# ARCHITECTURAL TRANSFORMATION:
# - Complete rewrite: SongBot.py → Modular Discord.py Cogs system
# - New project structure: config/, utils/, cogs/ modules
# - Centralized configuration in config/settings.py
# - Modular commands: music, collection, admin, requests in separate cogs
#
# BRAND NEW GUI APPLICATION:
# - Standalone tkinter-based control panel replacing command-line interface
# - Auto-start bot functionality with real-time monitoring
# - Live dashboard: bot status, logs, collection statistics, search counter
# - GUI admin controls: collection refresh and track history via buttons
# - Dynamic interface with auto-sizing elements for optimal display
#
# ROBUST DISTRIBUTION SYSTEM:
# - PyInstaller integration with build.py and build.bat
# - Portable executable that runs from any directory
# - Auto-create .env from template on first run with user guidance
# - Template value detection with configuration warnings
# - Two-step setup: create config file, then launch
#
# MODERNIZATION & CLEANUP:
# - Migrated admin functions from Discord commands to GUI buttons
# - Enhanced error handling with robust PyInstaller compatibility
# - Smart file management with automatic creation relative to executable
# - Clean output with organized logging and color coding
# - Fast Discord disconnect with proper cleanup
# - Cross-platform support for development and compiled modes

# -----------------------------------------------------------------------------
# Version 0.13 - Code quality improvements (2025-06-15)
# -----------------------------------------------------------------------------
# - Fixed all lint/type errors for enhanced code safety
# - Added proper null checks for Discord objects (channel, guild, user)
# - Improved type annotations with explicit list declarations
# - Enhanced XML parsing with null safety for location elements
# - Added robust TOKEN validation before bot startup
# - Fixed environment variable type handling and splitting logic

# -----------------------------------------------------------------------------
# Version 0.12 - Dynamic Traktor version detection (2025-06-15)
# -----------------------------------------------------------------------------
# - Automatic detection of latest Traktor version folder
# - Enhanced path management and future-proofing
# - Improved collection file handling

# -----------------------------------------------------------------------------
# Version 0.11 - Live streaming notifications (2025-06-15)  
# -----------------------------------------------------------------------------
# - Enhanced filtering system for better search results
# - Added live streaming notifications with role mentions
# - Community features for enhanced user interaction

# -----------------------------------------------------------------------------
# Version 0.10 - Complete song request management (2025-06-15)
# -----------------------------------------------------------------------------
# - Full CRUD operations for song requests
# - Enhanced command naming consistency
# - Improved user permission handling

# -----------------------------------------------------------------------------
# Version 0.9 - Interactive song request system (2025-06-15)
# -----------------------------------------------------------------------------
# - Major code reorganization for better maintainability
# - Interactive song selection with timeout handling
# - Enhanced user experience for song requests

# -----------------------------------------------------------------------------
# Earlier Versions (0.1 - 0.8)
# -----------------------------------------------------------------------------
# - 0.8: NowPlaying integration and history management
# - 0.7: Enhanced search algorithm and code organization  
# - 0.6: Major robustness improvements and debugging capabilities
# - 0.5: Enhanced text formatting and improved user feedback
# - 0.4: Configurable new songs tracking with date filtering
# - 0.3: New songs discovery and enhanced collection management
# - 0.2: Core functionality improvements
# - 0.1: Basic search functionality
