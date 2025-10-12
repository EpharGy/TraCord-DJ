"""
TraCord DJ - Simple Launcher
A simple launcher script for the GUI application
"""
import sys
import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox

from tracord.infra.logging import setup_for_environment
from utils.logger import info, warning, error

def ensure_settings_file():
    """Ensure data/settings.json exists, copying from settings_example.json if needed."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    settings_path = os.path.join(data_dir, 'settings.json')
    example_path = os.path.join(data_dir, 'settings_example.json')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        info(f"Created data directory at {data_dir}")
    if not os.path.exists(settings_path):
        if os.path.exists(example_path):
            try:
                shutil.copy(example_path, settings_path)
                info(f"Created new settings.json from example at {settings_path}")
            except Exception as e:
                error(f"Failed to copy settings_example.json: {e}")
                tk.Tk().withdraw()
                messagebox.showerror("Error", f"Could not create settings.json: {e}")
                sys.exit(1)
        else:
            error(f"settings_example.json not found in data directory: {example_path}")
            tk.Tk().withdraw()
            messagebox.showerror("Error", f"Missing settings_example.json in data directory: {example_path}\nCannot create settings.json.")
            sys.exit(1)

def main():
    """Main launcher function"""
    setup_for_environment()
    ensure_settings_file()
    # Create a minimal window for error messages
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    info("🚀 TraCord DJ Launcher")
    info("=" * 40)
    
    info("🚀 Starting GUI application...")
    
    # Close the hidden window
    root.destroy()
    
    try:
        # Set working directory to script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Forward all command-line arguments (except the script name itself) to gui.py
        gui_args = [sys.executable, 'gui.py'] + sys.argv[1:]
        subprocess.run(gui_args, check=True, cwd=script_dir)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Error running GUI: {e}")
    except FileNotFoundError:
        messagebox.showerror("Error", "Python not found! Please ensure Python is installed.")
    except KeyboardInterrupt:
        warning("🛑 Interrupted by user")

if __name__ == "__main__":
    main()
