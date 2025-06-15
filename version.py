"""
Version and Changelog for Traktor DJ NowPlaying Discord Bot

This file contains the current version and complete changelog.
For the latest version information, check this file or the GUI application.
"""

__version__ = "1.1.1"
__version_info__ = (1, 1, 1)

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
# Version 1.1.1 - PATCH RELEASE (2025-06-16)
# -----------------------------------------------------------------------------
# Critical Discord message limit fixes and search optimization
#
# BUG FIXES:
# - Fixed Discord 2000-character message limit causing search timeouts
# - Resolved "hasu" search timeout issue (was message length, not search performance)
# - Fixed incorrect result count displays in truncation messages
# - Corrected message formatting (truncation info now on separate line)
#
# PERFORMANCE IMPROVEMENTS:
# - Removed artificial MAX_SONGS limit - now dynamically fits maximum results
# - Implemented smart message truncation with precise character counting
# - Two-pass algorithm for optimal result fitting within Discord limits
# - Dynamic message length calculation for both truncated and non-truncated scenarios
#
# ENHANCEMENTS:
# - Improved user feedback with accurate "showing X of Y results" messages
# - Enhanced collection display with smart truncation for new songs feature
# - Better debug logging for message length monitoring
# - Consistent 2000-character limit handling across all Discord responses
#
# TECHNICAL DETAILS:
# - Dynamic string length calculation instead of fixed buffers
# - Precise character counting for message components
# - Optimal result fitting algorithm maximizes displayed songs
# - Proper line formatting for professional Discord message appearance

# -----------------------------------------------------------------------------
# Version 1.1.0 - MINOR RELEASE (2025-06-15)
# -----------------------------------------------------------------------------
# Major performance optimization and architectural enhancement
# 
# PERFORMANCE IMPROVEMENTS:
# - Converted XML collection parsing to optimized JSON format for 10x+ faster searches
# - Fixed Discord interaction timeout errors for searches like "hasu" and "hasunosora"
# - Implemented new workflow: XML → JSON conversion → fast JSON-based searches
# - Added collection.json to .gitignore (auto-generated file)
# - All search and collection functions now use lightning-fast JSON parsing
#
# NEW FEATURES & ENHANCEMENTS:
# - Added COVERARTID field to collection data for future artwork features
# - Enhanced collection refresh workflow with better error handling
# - Improved memory efficiency and search performance
# - Future-ready data structure for upcoming enhancements
#
# CODE CLEANUP & MAINTENANCE:
# - Removed deprecated SongBot.py (old monolithic bot replaced by Cogs system)
# - Removed old "DJ Discord Bot.code-workspace" file (renamed for clarity)
# - Comprehensive audit and cleanup of unused files
# - Optimized codebase structure and imports
#
# ARCHITECTURAL CHANGES:
# - New JSON-based collection system with fields: artist, title, album, cover_art_id, import_date
# - Updated refresh workflow: copy XML → create JSON → delete temp XML
# - All search functions (song search, new songs, collection stats) now use JSON
# - Enhanced modularity and maintainability
#
# BUG FIXES:
# - Fixed "The application did not respond" timeout errors on Discord searches
# - Resolved slow search performance for terms with many matches
# - Fixed collection refresh workflow for better reliability

# -----------------------------------------------------------------------------
# Version 1.0.3 - PATCH RELEASE (2025-06-15)
# -----------------------------------------------------------------------------
# Complete rebranding and naming consistency
# 
# REBRANDING:
# - Repository renamed to "Traktor-DJ-NowPlaying-Discord-Bot" for clarity
# - Executable renamed to "Traktor-DJ-NowPlaying-Discord-Bot-GUI.exe"
# - Updated all GUI titles and messages with new branding
# - Updated all documentation and build scripts with new naming
# - Consistent branding across all application interfaces
# - Better describes the bot's actual functionality (Traktor + NowPlaying + Discord)

# -----------------------------------------------------------------------------
# Version 1.0.2 - PATCH RELEASE (2025-06-15)
# -----------------------------------------------------------------------------
# Documentation streamlining and build improvements
# 
# IMPROVEMENTS:
# - Streamlined README.md by 50%+ - removed lengthy version sections
# - Centralized all version/changelog information in version.py
# - Moved Commands section after Quick Start for better user flow
# - Switched to static executable naming for simplicity
# - Updated build.py and RELEASE.md to use static naming
# - Simplified setup instructions and distribution notes
# - README now focuses on essentials with clear version.py reference

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

# =============================================================================
# Earlier Versions (0.1 - 1.0.0)
# =============================================================================
# - 1.0.0: Complete rewrite - Modular GUI application with cogs system and distribution
# - 0.13: Code quality improvements with enhanced null safety and type annotations
# - 0.12: Dynamic Traktor version detection with enhanced path management
# - 0.11: Live streaming notifications with role mentions and community features
# - 0.10: Complete song request management with full CRUD operations
# - 0.9: Interactive song request system - Major code reorganization, timeout handling
# - 0.8: NowPlaying integration and history management
# - 0.7: Enhanced search algorithm and code organization  
# - 0.6: Major robustness improvements and debugging capabilities
# - 0.5: Enhanced text formatting and improved user feedback
# - 0.4: Configurable new songs tracking with date filtering
# - 0.3: New songs discovery and enhanced collection management
# - 0.2: Core functionality improvements
# - 0.1: Basic search functionality
