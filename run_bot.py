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

def check_requirements():
    """Check if all requirements are met"""
    issues = []
    
    # Use script directory for all checks
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're in the right directory
    if not os.path.exists(os.path.join(base_dir, 'config', 'settings.py')):
        issues.append("❌ Bot files not found! Please ensure you're in the TraCord DJ directory.")
    
    # Check if .env file exists
    if not os.path.exists(os.path.join(base_dir, '.env')):
        issues.append("❌ .env file not found! Please create a .env file with your Discord bot token.")
    
    # Check if GUI file exists
    if not os.path.exists(os.path.join(base_dir, 'gui.py')):
        issues.append("❌ gui.py not found! The GUI application file is missing.")
    
    return issues

def main():
    """Main launcher function"""
    # Create a minimal window for error messages
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    info("🚀 TraCord DJ Launcher")
    info("=" * 40)
    
    # Check requirements
    issues = check_requirements()
    if issues:
        error_msg = "\\n".join(issues)
        warning(error_msg)
        messagebox.showerror("Setup Error", error_msg)
        return
    
    info("✅ All requirements met")
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
