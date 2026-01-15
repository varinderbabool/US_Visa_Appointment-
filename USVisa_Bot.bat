@echo off
REM ============================================================
REM US Visa Appointment Bot - Launcher
REM ============================================================
REM This launcher will:
REM   - Show GUI window for bot control and configuration
REM   - Show Chrome browser (visible, not headless) for automation
REM   - Show console window for detailed logs and debugging
REM ============================================================
REM Double-click this file to start the bot
REM ============================================================
REM Features:
REM   - Optimized calendar interactions (JavaScript-based)
REM   - Automatic retry from home page when no dates found
REM   - System busy detection only when calendar fails to open
REM   - 30-second wait only on home page during retries
REM   - Telegram notifications for each attempt number
REM   - Retry from home if time dropdown is empty
REM   - Proper stop functionality (Stop button or /stop) closes Chrome and ends process
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   US Visa Appointment Bot - Starting...
echo ============================================================
echo.
echo This console window will show detailed logs from the bot.
echo The GUI window will open separately for configuration.
echo Chrome browser will be visible when bot runs (not headless).
echo.
echo Features:
echo   - Optimized calendar interactions (JavaScript-based)
echo   - Automatic retry mechanism from home page
echo   - Real-time log monitoring
echo   - Telegram notifications for each attempt number
echo   - Retry from home if time dropdown is empty
echo   - Proper stop functionality (Stop button or /stop closes Chrome)
echo.
echo ============================================================
echo.

set "USE_TELEGRAM_INPUTS=false"
set /p USE_TG="Use Telegram inputs? (y/N): "
if /I "%USE_TG%"=="Y" set "USE_TELEGRAM_INPUTS=true"
if /I "%USE_TG%"=="YES" set "USE_TELEGRAM_INPUTS=true"

python gui.py

REM If Python is not found, show error
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   ERROR: Python not found or gui.py failed to run!
    echo ============================================================
    echo.
    echo Please make sure:
    echo   1. Python is installed (Python 3.7 or higher)
    echo   2. Python is added to PATH
    echo   3. All dependencies are installed
    echo      Run: pip install -r requirements.txt
    echo.
    echo Required packages:
    echo   - selenium
    echo   - python-telegram-bot
    echo   - python-dotenv
    echo   - tkcalendar
    echo.
    echo ============================================================
    echo.
    pause
)
