"""
TraCord DJ - Simple Launcher
A simple launcher script for the GUI application
"""
import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from utils.logger import info, warning, error

def main():
    """Main launcher function"""
    # Create a minimal window for error messages
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    info("🚀 TraCord DJ Launcher")
    info("=" * 40)
    
    info("🚀 Starting GUI application...")
    
    # Close the hidden window
    root.destroy()
    
    try:
        # Launch the GUI
        subprocess.run([sys.executable, 'gui.py'], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Error running GUI: {e}")
    except FileNotFoundError:
        messagebox.showerror("Error", "Python not found! Please ensure Python is installed.")
    except KeyboardInterrupt:
        warning("🛑 Interrupted by user")

if __name__ == "__main__":
    main()
