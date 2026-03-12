@echo off
echo ====================================
echo MTK Firmware Editor Pro - Launcher
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Starting MTK Firmware Editor Pro...
echo.

REM Run the application
python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    echo Check the log files in the logs directory for details
    pause
)
