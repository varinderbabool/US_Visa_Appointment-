"""Settings configuration for US Visa Appointment Bot."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Account Info
NUM_PARTICIPANTS = 1

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Visa Website Credentials
USER_EMAIL = os.getenv('VISA_EMAIL', '')
USER_PASSWORD = os.getenv('VISA_PASSWORD', '')
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

# Browser Settings
SHOW_GUI = os.getenv('HEADLESS', 'false').lower() != 'true'  # Show browser window
DETACH = False  # Keep browser open after script ends

# Timing Settings
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '30'))  # Check interval in seconds (default: 30 seconds)
TIMEOUT = 10  # Selenium timeout in seconds
NEW_SESSION_AFTER_FAILURES = 5  # Create new session after N failures
NEW_SESSION_DELAY = 60  # Delay before starting new session (seconds)
FAIL_RETRY_DELAY = 30  # Delay before retrying after failure (seconds)

# Retry Settings
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '10'))  # seconds

# State file for storing preferences
STATE_FILE = os.getenv('STATE_FILE', 'appointment_state.json')

# Test Mode (set to True to test without actually booking)
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
