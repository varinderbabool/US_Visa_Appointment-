# US Visa Appointment Automation Bot

An automated bot that monitors US visa appointment availability and books appointments based on Telegram notifications and confirmations.

## Features

- 🤖 Automated monitoring of US visa appointment availability
- 📱 Telegram bot integration for notifications and confirmations
- ⏰ Configurable check intervals (default: 5 minutes)
- 🔄 Automatic retry logic for failed operations
- 💾 State persistence for counselor/region selection
- 📝 Comprehensive logging

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser (for Selenium)
- Telegram account
- US visa appointment account credentials

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install ChromeDriver

The script uses Selenium with Chrome. ChromeDriver should be installed automatically, but if you encounter issues:

- **Windows**: Download from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)
- **macOS**: `brew install chromedriver`
- **Linux**: `sudo apt-get install chromium-chromedriver`

### 3. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Send a message to your bot to start a chat
6. Get your Chat ID:
   - Search for [@userinfobot](https://t.me/userinfobot) on Telegram
   - Send `/start` to get your Chat ID (looks like: `123456789`)

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following content:

```env
# Visa Website Credentials
VISA_EMAIL=your_email@example.com
VISA_PASSWORD=your_password

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Check interval in seconds (default: 300 = 5 minutes)
CHECK_INTERVAL=300

# Browser settings
HEADLESS=false
BROWSER_TYPE=chrome

# Retry settings
MAX_RETRIES=3
RETRY_DELAY=10

# State file location
STATE_FILE=appointment_state.json

# Appointment settings
EARLIEST_ACCEPTABLE_DATE=2025-01-01
LATEST_ACCEPTABLE_DATE=2025-12-31
CURRENT_BOOKING_DATE=2025-12-31
LOCATION=Toronto
```

**Important**: Never commit your `.env` file to version control!

## Usage

### Running the Bot

```bash
python main.py
```

### First Run

1. The bot will log in to the visa appointment website
2. You'll be prompted to select a counselor/region:
   - If counselors are detected automatically, select from the list
   - Otherwise, enter the counselor/region ID manually
3. The bot starts monitoring for available appointments

### How It Works

1. **Initialization**: Bot logs in and selects your preferred counselor/region
2. **Monitoring**: Every 5 minutes (configurable), the bot checks for available dates
3. **Notification**: When a date becomes available, you'll receive a Telegram message
4. **Confirmation**: Reply with `yes` to book the appointment or `no` to skip
5. **Booking**: If confirmed, the bot attempts to book the appointment automatically

### Telegram Commands

- `/start` - Start the bot and see welcome message
- `/status` - Check current bot status

### Telegram Responses

When a date is available, reply with:
- `yes`, `y`, `confirm`, `ok`, or `book` - Confirm and book the appointment
- `no`, `n`, `cancel`, or `skip` - Skip this date and continue monitoring

## Configuration Options

### Check Interval

Control how often the bot checks for availability:

```env
CHECK_INTERVAL=300  # 5 minutes (default)
CHECK_INTERVAL=600  # 10 minutes
CHECK_INTERVAL=180  # 3 minutes
```

### Headless Mode

Run the browser in the background (no visible window):

```env
HEADLESS=true
```

### Logging

Logs are written to:
- Console output (stdout)
- `visa_bot.log` file

## Important Notes

### Website Structure

⚠️ **Important**: The actual website selectors and workflow may need adjustment based on the current structure of `ais.usvisa-info.com`. The script includes multiple selector strategies, but you may need to:

1. Inspect the website structure
2. Update selectors in `visa_scraper.py` if needed
3. Test thoroughly before production use

### Legal Compliance

⚠️ **Warning**: Ensure this automation complies with the website's terms of service. Use responsibly and at your own risk.

### Rate Limiting

The bot includes delays between operations to be respectful of the website. Adjust retry settings if needed:

```env
MAX_RETRIES=3
RETRY_DELAY=10  # seconds between retries
```

## Troubleshooting

### Login Issues

- Verify your credentials in `.env`
- Check if the website structure has changed
- Try running with `HEADLESS=false` to see what's happening
- Check `visa_bot.log` for detailed error messages

### Telegram Bot Not Working

- Verify your bot token and chat ID
- Make sure you've started a chat with your bot
- Check that you're using the correct chat ID (your personal chat ID, not the bot's)

### Browser/Driver Issues

- Ensure Chrome is installed and up to date
- Update ChromeDriver if needed
- Try installing ChromeDriver manually
- Check `visa_bot.log` for Selenium errors

### No Dates Found

- This is normal if no appointments are available
- The bot will continue checking automatically
- Verify you've selected the correct counselor/region

## File Structure

```
USVisa/
├── main.py                 # Main entry point
├── config.py               # Configuration management
├── visa_scraper.py         # Web scraping and automation
├── telegram_bot.py         # Telegram bot integration
├── state_manager.py        # State persistence
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── visa_bot.log           # Log file (generated)
└── appointment_state.json # State file (generated)
```

## Development

### Testing Selectors

To test and debug selectors, run the script with `HEADLESS=false` to see the browser in action.

### Adding New Features

The code is modular:
- `visa_scraper.py` - Web automation logic
- `telegram_bot.py` - Telegram integration
- `state_manager.py` - State management
- `config.py` - Configuration

## License

This project is for personal use. Use at your own risk.

## Support

For issues and questions:
1. Check the `visa_bot.log` file for error messages
2. Verify all configuration settings
3. Ensure dependencies are installed correctly

## Disclaimer

This bot is provided as-is for educational and personal use. The authors are not responsible for any issues that may arise from using this automation. Always verify appointments manually and ensure compliance with the website's terms of service.
