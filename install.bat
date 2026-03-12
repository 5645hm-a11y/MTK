@echo off
echo ====================================
echo MTK Firmware Editor Pro - Installer
echo ====================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Installing required packages...
echo This may take a few minutes...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo You can now run the application using:
echo   - run.bat (Windows)
echo   - python main.py (Command line)
echo.
pause
