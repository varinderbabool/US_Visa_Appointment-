# US Visa Appointment Automation Bot

An automated bot that monitors US visa appointment availability and books appointments automatically. Features both CLI and GUI interfaces.

## Features

- 🤖 Automated monitoring of US visa appointment availability
- 📱 Telegram bot integration for notifications
- 🖥️ **GUI Interface** - Easy-to-use graphical interface
- ⏰ Configurable check intervals (default: 30 seconds)
- 🔄 Automatic retry logic for failed operations
- 💾 State persistence for preferences
- 📝 Comprehensive logging
- 🎯 Automatic booking when slots are found

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser (for Selenium)
- Telegram account (optional, for notifications)
- US visa appointment account credentials

## Quick Start (GUI)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the GUI**
   - **Windows**: Double-click `USVisa_Bot.bat` or `USVisa_Bot.vbs`
   - **Command Line**: `python gui.py`

3. **Enter Your Details**
   - Email and Password
   - Location (consulate)
   - Date ranges (Earliest, Latest, Current Booking Date)

4. **Click "Start Bot"**

The bot will automatically monitor and book appointments when available!

## Setup (CLI Mode)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install ChromeDriver

ChromeDriver should be installed automatically, but if you encounter issues:

- **Windows**: Download from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)
- **macOS**: `brew install chromedriver`
- **Linux**: `sudo apt-get install chromium-chromedriver`

### 3. Configure Environment Variables (Optional)

Create a `.env` file in the project root:

```env
# Visa Website Credentials
VISA_EMAIL=your_email@example.com
VISA_PASSWORD=your_password

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Check interval in seconds (default: 30)
CHECK_INTERVAL=30

# Date Settings
EARLIEST_ACCEPTABLE_DATE=2026-01-31
LATEST_ACCEPTABLE_DATE=2026-12-31
CURRENT_BOOKING_DATE=2027-06-30
LOCATION=Toronto
```

**Note**: The GUI mode prompts for these values, so `.env` is optional when using GUI.

## Usage

### GUI Mode (Recommended)

1. Run `python gui.py` or double-click `USVisa_Bot.bat`
2. Fill in the form fields
3. Click "Start Bot"
4. Monitor the logs in the GUI window

### CLI Mode

```bash
python main.py
```

The bot will prompt you for:
- Email and Password
- Telegram Chat ID (optional)
- Location selection

## How It Works

1. **Login**: Bot logs in to the visa appointment website
2. **Navigation**: Navigates to the reschedule appointment page
3. **Location Selection**: Selects your preferred consulate location
4. **Monitoring**: Continuously checks for available dates
5. **Booking**: Automatically books when a suitable date is found (earlier than current booking and within date range)
6. **Notifications**: Sends Telegram notifications for status updates

## File Structure

```
USVisa/
├── main.py                 # Main entry point (CLI)
├── gui.py                  # GUI interface
├── settings.py             # Configuration settings
├── visa_scraper.py         # Web scraping and automation
├── telegram_bot.py         # Telegram bot integration
├── state_manager.py        # State persistence
├── requirements.txt        # Python dependencies
├── USVisa_Bot.bat         # Windows launcher (GUI)
├── USVisa_Bot.vbs         # Windows launcher (silent)
├── USVisa_Bot.pyw         # Python windowed launcher
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── CODE_REVIEW.md         # Code review documentation
```

## Important Notes

### Legal Compliance

⚠️ **Warning**: Ensure this automation complies with the website's terms of service. Use responsibly and at your own risk.

### Website Structure

⚠️ **Important**: The website structure may change. If the bot stops working, check `visa_bot.log` for errors and update selectors in `visa_scraper.py` if needed.

## Troubleshooting

### GUI Not Opening
- Ensure Python and tkinter are installed
- Install tkcalendar: `pip install tkcalendar`
- Check for error messages in console

### Login Issues
- Verify your credentials
- Check if the website structure has changed
- Review `visa_bot.log` for detailed errors

### Telegram Notifications Not Working
- Verify bot token and chat ID
- Ensure you've started a chat with your bot

## License

This project is for personal use. Use at your own risk.

## Disclaimer

This bot is provided as-is for educational and personal use. The authors are not responsible for any issues that may arise from using this automation. Always verify appointments manually and ensure compliance with the website's terms of service.
