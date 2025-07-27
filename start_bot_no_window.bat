@echo off
title TraCord DJ
cd /d "%~dp0"

echo.
echo ========================================
echo    TraCord DJ - Windows Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    echo.
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "run_bot.py" (
    echo ERROR: run_bot.py not found!
    echo Please ensure you're in the TraCord DJ directory.
    echo.
    pause
    exit /b 1
)

echo Starting TraCord DJ GUI...
echo.

REM Start the GUI application
start "" pythonw.exe run_bot.py
