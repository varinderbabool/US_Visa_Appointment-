"""Configuration management for US Visa Appointment Bot."""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Configuration class to store all settings."""
    
    # Visa website credentials
    VISA_EMAIL = os.getenv('VISA_EMAIL', '')
    VISA_PASSWORD = os.getenv('VISA_PASSWORD', '')
    VISA_URL = os.getenv('VISA_URL', 'https://ais.usvisa-info.com/en-ca/niv/users/sign_in')
    
    # Telegram bot settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Check interval in seconds (default: 5 minutes)
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '30'))
    
    # Browser settings
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    BROWSER_TYPE = os.getenv('BROWSER_TYPE', 'chrome')  # 'chrome' or 'firefox'
    
    # Retry settings
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '10'))  # seconds
    
    # State file for storing preferences
    STATE_FILE = os.getenv('STATE_FILE', 'appointment_state.json')
    
    # Appointment settings
    MAX_DATE = os.getenv('MAX_DATE', '2026-12-31').strip() or None  # Maximum date to check for appointments
    LOCATION = os.getenv('LOCATION', 'Toronto').strip() or 'Toronto'  # Consular section location
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        missing = []
        
        if not cls.VISA_EMAIL:
            missing.append('VISA_EMAIL')
        if not cls.VISA_PASSWORD:
            missing.append('VISA_PASSWORD')
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        # TELEGRAM_CHAT_ID is optional - will be auto-detected if not set
        if not cls.TELEGRAM_CHAT_ID:
            logger.warning("TELEGRAM_CHAT_ID not set - will be auto-detected from first message")
            cls.TELEGRAM_CHAT_ID = '0'  # Placeholder that will be replaced
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
