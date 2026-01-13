@echo off
REM US Visa Appointment Bot - GUI Launcher
REM Double-click this file to start the bot

cd /d "%~dp0"
python gui.py

REM If Python is not found, show error
if errorlevel 1 (
    echo.
    echo ERROR: Python not found or gui.py failed to run!
    echo Please make sure Python is installed and added to PATH.
    echo.
    pause
)
