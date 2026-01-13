#!/usr/bin/env python3
"""Main script for US Visa Appointment Automation Bot."""
import logging
import time
import sys
from datetime import datetime, date
from typing import Optional, Dict, Any
from settings import (
    USER_EMAIL, USER_PASSWORD, LOGIN_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    EARLIEST_ACCEPTABLE_DATE, LATEST_ACCEPTABLE_DATE, CURRENT_BOOKING_DATE,
    USER_CONSULATE, CONSULATES, CHECK_INTERVAL, SHOW_GUI, TIMEOUT, STATE_FILE
)
from visa_scraper import VisaScraper
from telegram_bot import TelegramNotifier
from state_manager import StateManager

# Configure logging with UTF-8 encoding to handle emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('visa_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# NOTE: The following functions are kept for potential future use but are currently unused
# They were part of the original interactive flow but are now replaced by GUI/input prompts

# def get_user_counselor_selection(scraper: VisaScraper, state_manager: StateManager) -> str:
#     """Interactive counselor/region selection."""
#     # ... (removed for clarity - kept in git history if needed)

# def get_user_date_range(state_manager: StateManager) -> Optional[str]:
#     """Interactive date range selection."""
#     # ... (removed for clarity - kept in git history if needed)


def get_user_inputs() -> Dict[str, Any]:
    """Get user inputs interactively before starting the bot.
    
    Returns:
        Dictionary containing user inputs: email, password, telegram_token,
        telegram_chat_id, location, earliest_date, latest_date, current_date, check_interval
    """
    print("\n" + "="*60)
    print("US Visa Appointment Bot - Configuration")
    print("="*60)
    print("Please provide the following information:\n")
    
    inputs = {}
    
    # 1. Email
    import getpass
    while True:
        try:
            email = input("1. Enter your visa account email: ").strip()
            if email and '@' in email and '.' in email.split('@')[1]:
                inputs['email'] = email
                break
            print("   ❌ Invalid email format. Please try again.")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)
    
    # 2. Password
    while True:
        try:
            password = getpass.getpass("2. Enter your visa account password: ").strip()
            if password and len(password) >= 1:
                inputs['password'] = password
                break
            print("   ❌ Password cannot be empty. Please try again.")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)
    
    # 3. Telegram Chat ID (optional)
    chat_id = input("3. Enter your Telegram Chat ID (or press Enter to use default: 2023815877): ").strip()
    inputs['telegram_chat_id'] = chat_id if chat_id else '2023815877'
    
    # 4. Location/Consulate
    print("\n4. Select consulate location:")
    consulates_list = list(CONSULATES.keys())
    for i, loc in enumerate(consulates_list, 1):
        print(f"   {i}. {loc}")
    
    while True:
        try:
            choice = input(f"   Enter choice (1-{len(consulates_list)}) [default: Toronto]: ").strip()
            if not choice:
                inputs['location'] = 'Toronto'
                break
            choice_num = int(choice)
            if 1 <= choice_num <= len(consulates_list):
                inputs['location'] = consulates_list[choice_num - 1]
                break
            print(f"   ❌ Please enter a number between 1 and {len(consulates_list)}")
        except ValueError:
            print("   ❌ Invalid input. Please enter a number.")
    
    # Set fixed values (not prompted)
    inputs['telegram_token'] = '8035456582:AAGFF8HJBjepiL7eg_oIEVwdMQmWWCiJIkA'
    inputs['earliest_date'] = '2026-01-31'
    inputs['latest_date'] = '2026-12-31'
    inputs['current_date'] = '2027-06-30'
    inputs['check_interval'] = 30
    
    print("\n" + "="*60)
    print("Configuration Summary:")
    print("="*60)
    print(f"Email: {inputs['email']}")
    print(f"Password: {'*' * len(inputs['password'])}")
    print(f"Telegram Token: {inputs['telegram_token'][:10]}...")
    print(f"Telegram Chat ID: {inputs['telegram_chat_id'] if inputs['telegram_chat_id'] != '0' else 'Auto-detect'}")
    print(f"Location: {inputs['location']}")
    print(f"Earliest Date: {inputs['earliest_date']} (fixed)")
    print(f"Latest Date: {inputs['latest_date']} (fixed)")
    print(f"Current Booking: {inputs['current_date']} (fixed)")
    print(f"Check Interval: {inputs['check_interval']} seconds (fixed)")
    print("="*60)
    
    confirm = input("\nProceed with these settings? (yes/no) [default: yes]: ").strip().lower()
    if confirm and confirm not in ['yes', 'y', '']:
        print("Configuration cancelled.")
        sys.exit(0)
    
    return inputs


def update_settings_dates(new_date_str: str) -> None:
    """Update CURRENT_BOOKING_DATE and LATEST_ACCEPTABLE_DATE in settings.py after successful booking.
    
    Args:
        new_date_str: New booking date in YYYY-MM-DD format
        
    Raises:
        IOError: If file cannot be read or written
        ValueError: If date format is invalid
    """
    # Validate date format
    try:
        datetime.strptime(new_date_str, "%Y-%m-%d")
    except ValueError:
        logger.error(f"[ERROR] Invalid date format: {new_date_str}. Expected YYYY-MM-DD")
        raise ValueError(f"Invalid date format: {new_date_str}. Expected YYYY-MM-DD")
    
    try:
        # Read current settings
        with open("settings.py", "r", encoding='utf-8') as f:
            lines = f.readlines()

        # Write updated settings
        with open("settings.py", "w", encoding='utf-8') as f:
            for line in lines:
                if line.strip().startswith("CURRENT_BOOKING_DATE"):
                    f.write(f'CURRENT_BOOKING_DATE = os.getenv(\'CURRENT_BOOKING_DATE\', \'{new_date_str}\')\n')
                elif line.strip().startswith("LATEST_ACCEPTABLE_DATE"):
                    f.write(f'LATEST_ACCEPTABLE_DATE = os.getenv(\'LATEST_ACCEPTABLE_DATE\', \'{new_date_str}\')\n')
                else:
                    f.write(line)

        logger.info(f"[INFO] settings.py updated with new booking date: {new_date_str}")
    except IOError as e:
        logger.error(f"[ERROR] Failed to update settings.py: {e}")
        raise
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error updating settings.py: {e}")
        raise


def main(gui_inputs: Optional[Dict[str, Any]] = None) -> None:
    """Main function to run the US Visa Appointment Bot.
    
    Args:
        gui_inputs: Optional dictionary of inputs from GUI. If provided, skips interactive prompts.
                   Expected keys: email, password, telegram_token, telegram_chat_id, location,
                   earliest_date, latest_date, current_date, check_interval
    """
    logger.info("Starting US Visa Appointment Bot")
    
    # Get user inputs interactively or from GUI
    if gui_inputs:
        # Use inputs from GUI
        user_inputs = gui_inputs
        logger.info("Using inputs from GUI")
    else:
        # Get user inputs interactively
        user_inputs = get_user_inputs()
    
    # Use user inputs (override settings)
    email = user_inputs['email']
    password = user_inputs['password']
    telegram_token = user_inputs['telegram_token']
    telegram_chat_id = user_inputs['telegram_chat_id']
    location = user_inputs['location']
    earliest_date = user_inputs['earliest_date']
    latest_date = user_inputs['latest_date']
    current_booking_date = user_inputs['current_date']
    check_interval = user_inputs['check_interval']
    
    # Initialize components
    state_manager = StateManager(STATE_FILE)
    telegram_bot = None
    scraper = None
    
    try:
        # Initialize Telegram bot
        logger.info("Initializing Telegram bot...")
        chat_id = telegram_chat_id if telegram_chat_id and str(telegram_chat_id) != '0' else '0'
        telegram_bot = TelegramNotifier(telegram_token, chat_id)
        
        # If chat ID was not set, wait for user to send a message
        if chat_id == '0' or not chat_id:
            logger.info("TELEGRAM_CHAT_ID not set. Please send a message to your bot (e.g., /start)")
            logger.info("Waiting for chat ID to be detected...")
            print("\n⚠️  TELEGRAM_CHAT_ID not found!")
            print("Please send a message to your Telegram bot (e.g., /start)")
            print("The chat ID will be automatically detected...\n")
            # Wait up to 60 seconds for a message
            for i in range(60):
                time.sleep(1)
                if telegram_bot.chat_id and telegram_bot.chat_id != '0':
                    logger.info(f"Chat ID detected: {telegram_bot.chat_id}")
                    break
            if not telegram_bot.chat_id or telegram_bot.chat_id == '0':
                logger.error("Chat ID not detected. Please send a message to your bot and try again.")
                print("\n❌ Chat ID not detected. Please send a message to your bot and try again.")
                sys.exit(1)
        
        telegram_bot.send_sync("🤖 US Visa Appointment Bot started!")
        logger.info("Telegram bot initialized")
        
        # Initialize scraper
        logger.info("Initializing web scraper...")
        scraper = VisaScraper(
            email=email,
            password=password,
            url=LOGIN_URL,
            headless=not SHOW_GUI,
            browser_type='chrome'
        )
        
        # Login
        logger.info("Logging in to visa website...")
        if not scraper.login():
            logger.error("Failed to login")
            telegram_bot.send_sync("❌ Failed to login to visa website. Please check credentials.")
            sys.exit(1)
        
        logger.info("Login successful")
        telegram_bot.send_sync("✅ Successfully logged in to visa website!")
        
        # Click Continue button (goes to Groups page)
        logger.info("Clicking Continue button...")
        if not scraper.click_continue():
            logger.error("Failed to click Continue")
            telegram_bot.send_sync("❌ Failed to click Continue. Exiting.")
            sys.exit(1)
        
        # Extract existing appointment date from Groups page (optional)
        logger.info("Extracting existing appointment date from Groups page...")
        existing_date = scraper.get_existing_appointment_date()
        
        # Use latest_date from user input as max_date
        max_date = latest_date
        if existing_date:
            logger.info(f"Found existing appointment date: {existing_date}")
        
        # Set max_date in scraper
        scraper.set_max_date(max_date)
        
        # Parse date ranges from user inputs
        earliest_date_obj = datetime.strptime(earliest_date, "%Y-%m-%d").date()
        latest_date_obj = datetime.strptime(latest_date, "%Y-%m-%d").date()
        current_booking = datetime.strptime(current_booking_date, "%Y-%m-%d").date()
        
        telegram_bot.send_sync(
            f"✅ Monitoring appointments\n"
            f"📍 Location: {location}\n"
            f"📅 Date range: {earliest_date} to {latest_date}\n"
            f"📆 Current booking: {current_booking_date}\n"
            f"🔍 Looking for dates earlier than current booking..."
        )
        
        # Navigate to Reschedule Appointment
        logger.info("Navigating to Reschedule Appointment...")
        if not scraper.navigate_to_reschedule():
            logger.error("Failed to navigate to reschedule")
            telegram_bot.send_sync("❌ Failed to navigate to reschedule. Exiting.")
            sys.exit(1)
        
        # Get location selection from user input
        selected_location = location
        logger.info(f"Selecting location: {selected_location}")
        if not scraper.select_location(selected_location):
            logger.error("Failed to select location")
            # Check if it's due to system busy error
            if scraper.check_system_busy_error():
                logger.error("System is busy. Please try again later.")
                telegram_bot.send_sync("⚠️ <b>System is busy</b>\n\nPlease try again.")
                logger.info("Exiting due to system busy error")
                sys.exit(0)
            else:
                telegram_bot.send_sync("❌ Failed to select location. Exiting.")
                sys.exit(1)
        
        # Check for system busy error after selecting location
        if scraper.check_system_busy_error():
            logger.error("System is busy. Please try again later.")
            telegram_bot.send_sync("⚠️ <b>System is busy</b>\n\nPlease try again.")
            logger.info("Exiting due to system busy error")
            sys.exit(0)
        
        scraper.selected_counselor = selected_location
        scraper.counselor_selected = True
        
        logger.info(f"Monitoring for location: {selected_location}, max date: {max_date}")
        logger.info(f"Will only book if date is earlier than: {current_booking_date}")
        
        # Main monitoring loop
        logger.info(f"Starting monitoring loop (checking every {check_interval} seconds)")
        check_count = 0
        
        while True:
            try:
                check_count += 1
                logger.info(f"Check #{check_count}: Checking for available dates...")
                
                # Ensure we're on the appointment page
                current_url = scraper.driver.current_url
                if '/appointment' not in current_url:
                    logger.info("Not on appointment page, navigating to reschedule...")
                    scraper.navigate_to_reschedule()
                    scraper.select_location(selected_location)
                    time.sleep(2)
                
                # Check for system busy error before checking dates
                if scraper.check_system_busy_error():
                    logger.error("System is busy. Please try again later.")
                    telegram_bot.send_sync("⚠️ <b>System is busy</b>\n\nPlease try again.")
                    logger.info("Exiting due to system busy error")
                    sys.exit(0)
                
                # Check for available dates
                date_info = scraper.check_available_dates()
                
                if date_info:
                    found_date_str = date_info.get('date', '')
                    found_location = date_info.get('location', 'Unknown')
                    
                    try:
                        found_date = datetime.strptime(found_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        logger.warning(f"Invalid date format: {found_date_str}")
                        continue
                    
                    logger.info(f"Available date found: {found_date_str} at {found_location}")
                    
                    # Check if date is within acceptable range
                    if found_date < earliest_date_obj or found_date > latest_date_obj:
                        logger.info(f"Found date {found_date_str} not within acceptable range ({earliest_date} to {latest_date})")
                        continue
                    
                    # Check if date is earlier than current booking
                    if found_date >= current_booking:
                        logger.info(f"Skipping booking. Found date {found_date_str} is not earlier than current booking {current_booking_date}")
                        continue
                    
                    # Format date info for Telegram
                    date_message = (
                        f"📅 <b>Date:</b> {found_date_str}\n"
                        f"📍 <b>Location:</b> {found_location}"
                    )
                    
                    # Notify user that date is available and booking is starting
                    logger.info(f"FOUND SLOT ON {found_date_str}, location: {found_location}. Attempting to book...")
                    telegram_bot.send_sync(
                        f"🎯 <b>New slot found: {found_date_str} @ {found_location}</b>\n\n"
                        f"✅ Date: {found_date_str}\n"
                        f"📍 Location: {found_location}\n\n"
                        f"⏳ Now attempting to book the appointment..."
                    )
                    
                    # Book appointment immediately (use first available time)
                    logger.info("Attempting to book appointment with first available time...")
                    
                    booking_success = scraper.book_appointment(date_info, preferred_time=None)
                    
                    if booking_success:
                        logger.info("Appointment booked successfully!")
                        telegram_bot.send_sync(
                            f"🎉 <b>Appointment Booked!</b>\n\n"
                            f"📅 Date: {found_date_str}\n"
                            f"📍 Location: {found_location}\n"
                            f"✅ Status: Confirmed"
                        )
                        # Update settings.py with new booking date
                        update_settings_dates(found_date_str)
                        logger.info("Appointment booking completed. Exiting.")
                        break
                    else:
                        logger.error("Failed to book appointment")
                        telegram_bot.send_sync(
                            f"⚠️ <b>Booking Failed!</b>\n\n"
                            f"Slot was found on {found_date_str} @ {found_location}, but failed to book.\n"
                            f"Please check manually."
                        )
                        # Go back to home and retry
                        scraper.go_to_home()
                        time.sleep(2)
                        scraper.click_continue()
                        scraper.navigate_to_reschedule()
                        scraper.select_location(selected_location)
                        time.sleep(2)
                else:
                    logger.debug("No available dates found - will retry")
                    # Go back to home and retry
                    logger.info("No dates found, going back to home and retrying...")
                    try:
                        if scraper.go_to_home():
                            logger.info("Successfully navigated to home")
                            time.sleep(1)
                            if scraper.click_continue():
                                logger.info("Successfully clicked Continue")
                                time.sleep(1)
                                if scraper.navigate_to_reschedule():
                                    logger.info("Successfully navigated to reschedule")
                                    time.sleep(1)
                                    if scraper.select_location(selected_location):
                                        logger.info("Successfully selected location - ready for next check")
                                        time.sleep(1)
                                    else:
                                        logger.warning("Failed to select location - will retry navigation in next cycle")
                                else:
                                    logger.warning("Failed to navigate to reschedule - will retry in next cycle")
                            else:
                                logger.warning("Failed to click Continue - will retry in next cycle")
                        else:
                            logger.warning("Failed to navigate to home - will retry in next cycle")
                    except Exception as e:
                        logger.error(f"Error during retry navigation: {e}", exc_info=True)
                        logger.info("Will retry navigation in next check cycle")
                    
                    # Wait before next check (continue the loop)
                    logger.info(f"Waiting {check_interval} seconds before next check...")
                    time.sleep(check_interval)
                    continue  # Continue to next iteration of the while loop
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                telegram_bot.send_sync("⚠️ Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                telegram_bot.send_sync(f"⚠️ Error occurred: {str(e)}. Continuing to monitor...")
                time.sleep(check_interval)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if telegram_bot:
            telegram_bot.send_sync(f"❌ Fatal error: {str(e)}")
    
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        if scraper:
            scraper.close()
        if telegram_bot:
            telegram_bot.stop()
        logger.info("Exiting")


if __name__ == "__main__":
    main()
