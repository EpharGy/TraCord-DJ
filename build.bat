@echo off
echo TraCord - Build GUI Executable for Distribution
echo =========================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Run the build script
python build.py

echo.
echo Build process completed!
echo Check the 'dist' folder for TraCord-DJ-GUI.exe
echo This file can be distributed to users without Python installed.
echo.
pause
