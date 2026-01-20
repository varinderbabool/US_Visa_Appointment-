# US Visa Appointment Automation Bot

An automated bot that monitors US visa appointment availability and books appointments automatically. Features both CLI and GUI interfaces.

## Features

- 🤖 Automated monitoring of US visa appointment availability
- 📱 Telegram bot integration for notifications
- 🖥️ **GUI Interface** - Easy-to-use graphical interface
- ⏰ Configurable check intervals (default: 5 seconds)
- 🔁 Optional two-location rotation (Location 1 + Location 2)
- 🔄 Automatic retry logic for failed operations
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
   - Location 1 (consulate) and optional Location 2
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

### 3. Configure Environment Variables

**IMPORTANT**: Create a `.env` file in the project root with your credentials:

1. Copy `env.example` to `.env`:
   ```bash
   copy env.example .env
   ```

2. Edit `.env` and fill in your values:
   ```env
   # Visa Website Credentials
   VISA_EMAIL=your_email@example.com
   VISA_PASSWORD=your_password

   # Telegram Bot Configuration (REQUIRED)
   # Get your bot token from @BotFather on Telegram
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=2023815877

   # Check interval in seconds (default: 5)
   CHECK_INTERVAL=5

   # Date Settings
   EARLIEST_ACCEPTABLE_DATE=2026-01-31
   LATEST_ACCEPTABLE_DATE=2026-12-31
   CURRENT_BOOKING_DATE=2027-06-30
   LOCATION=Toronto
   LOCATION_2=
   ```

**Security Note**: 
- The `.env` file is already in `.gitignore` and will NOT be committed to git
- Never commit your `.env` file or share it publicly
- The Telegram bot token is required - set it in `.env` file

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
- Location 1 and optional Location 2 selection

## How It Works

1. **Login**: Bot logs in to the visa appointment website
2. **Navigation**: Navigates to the reschedule appointment page
3. **Location Selection**: Selects your preferred consulate location(s)
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
