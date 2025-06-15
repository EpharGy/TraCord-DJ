@echo off
title DJ Discord Bot
cd /d "%~dp0"

echo.
echo ========================================
echo    DJ Discord Bot - Windows Launcher
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
if not exist "gui.py" (
    echo ERROR: gui.py not found!
    echo Please ensure you're in the DJ Discord Bot directory.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create a .env file with your Discord bot token.
    echo You can copy .env.example and fill in your values.
    echo.
    pause
    exit /b 1
)

echo Starting DJ Discord Bot GUI...
echo.

REM Start the GUI application
python gui.py

REM If we get here, the application has closed
echo.
echo Bot application closed.
pause
