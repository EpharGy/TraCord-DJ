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
if not exist "gui.py" (
    echo ERROR: gui.py not found!
    echo Please ensure you're in the TraCord DJ directory.
    echo.
    pause
    exit /b 1
)

echo Starting TraCord DJ GUI...
echo.

REM Start the GUI application
python gui.py

REM If we get here, the application has closed
echo.
echo Bot application closed.
pause
