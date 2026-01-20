"""Settings configuration for US Visa Appointment Bot."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
# IMPORTANT: Set these in .env file for security (never commit .env to git)
# Default values provided for convenience but should be overridden in .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('TELEGRAM_TOKEN', ''))
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '2023815877')

LOGIN_URL = os.getenv('VISA_URL', 'https://ais.usvisa-info.com/en-ca/niv/users/sign_in')

# Date Range Settings
# Earliest date you're willing to accept (YYYY-MM-DD format)
EARLIEST_ACCEPTABLE_DATE = os.getenv('EARLIEST_ACCEPTABLE_DATE', '2026-01-31')
# Latest date you're willing to accept (YYYY-MM-DD format)
LATEST_ACCEPTABLE_DATE = os.getenv('LATEST_ACCEPTABLE_DATE', '2026-12-31')
# Your current booking date - bot will only book if it finds an earlier date
CURRENT_BOOKING_DATE = os.getenv('CURRENT_BOOKING_DATE', '2027-06-30')

# Consulate/Location Settings
CONSULATES = {
    "Calgary": 89,
    "Halifax": 90,
    "Montreal": 91,
    "Ottawa": 92,
    "Quebec": 93,
    "Toronto": 94,
    "Vancouver": 95
}

# Your consulate's city (choose from CONSULATES above)
USER_CONSULATE = os.getenv('LOCATION', 'Toronto')
# Optional second consulate for alternating checks
USER_CONSULATE_2 = os.getenv('LOCATION_2', '')

# Browser Settings
SHOW_GUI = os.getenv('HEADLESS', 'false').lower() != 'true'  # Show browser window

# Timing Settings
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '5'))  # Check interval in seconds (default: 5 seconds)
