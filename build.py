#!/usr/bin/env python3
"""
Build script for creating standalone Traktor DJ NowPlaying Discord Bot executable
"""

import subprocess
import sys
import os
from pathlib import Path

# Import version information
try:
    from version import __version__
except ImportError:
    __version__ = "dev"

# === Build configuration variables ===
APP_NAME = "Traktor DJ NowPlaying Discord Bot"
EXE_NAME = "Traktor-DJ-NowPlaying-Discord-Bot-GUI"
ENTRY_POINT = "gui.py"
BUILD_FILENAME = "build.py"

def install_build_deps():
    """Install build dependencies"""
    print("Installing build dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"], check=True)

def build_gui_executable():
    """Build the GUI version using PyInstaller"""
    print(f"Building GUI executable for version {__version__}...")
    cmd = [
        "pyinstaller",
        "--onefile",                # Single executable file
        "--windowed",              # No console window (GUI app)
        f"--name={EXE_NAME}",
        "--icon=app_icon.ico",      # Add icon if available
        "--add-data=config;config",
        "--add-data=utils;utils",
        "--add-data=cogs;cogs",
        "--add-data=services;services",
        "--add-data=gui;gui",
        "--add-data=main.py;.",  # Explicitly include main.py
        "--add-data=version.py;.",
        "--add-data=.env.example;.",
        "--add-data=app_icon.ico;.",  # Include icon file in bundle
        "--add-data=icon.png;.",      # Include PNG icon as fallback
        "--hidden-import=discord",
        "--hidden-import=discord.ext.commands",
        "--hidden-import=tkinter",
        "--hidden-import=asyncio",
        "--hidden-import=main",     # Explicitly import main module
        "--hidden-import=config.settings",
        "--hidden-import=version",
        ENTRY_POINT
    ]
    # Remove icon parameter if icon file doesn't exist
    if not os.path.exists("app_icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]  # Remove icon argument
    
    subprocess.run(cmd, check=True)
    return EXE_NAME

def main():
    """Main build function"""
    print(f"{APP_NAME} - GUI Executable Build Script")
    print("=" * 70)
    print(f"Building version: {__version__}")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("main.py") or not os.path.exists(ENTRY_POINT):
        print("Error: Please run this script from the bot's root directory")
        sys.exit(1)
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage:")
        print(f"  python {BUILD_FILENAME} - Build GUI executable for distribution")
        print(f"  python {BUILD_FILENAME} --help - Show this help message")
        return
    
    try:
        # Install dependencies
        install_build_deps()
        
        # Build GUI executable only
        exe_name = build_gui_executable()
        
        print("\n" + "=" * 50)
        print("Build completed successfully!")
        print(f"Executable file is in the 'dist' directory:")
        print(f"- {exe_name}.exe (Version {__version__})")
        print("\n📦 Release Distribution:")
        print("1. Copy your .env file to the same directory as the executable")
        print("2. Test the executable on a clean system")
        print("3. Create a GitHub Release and upload the .exe file")
        print("4. Users can download and run without installing Python")
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
