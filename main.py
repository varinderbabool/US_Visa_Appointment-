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
import os
import threading
from visa_scraper import VisaScraper
from telegram_bot import TelegramNotifier
from state_manager import StateManager
from selenium.webdriver.common.by import By
from telegram_inputs import get_inputs_via_telegram

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
    # Get from settings or environment variables (not hardcoded for security)
    inputs['telegram_token'] = TELEGRAM_BOT_TOKEN if TELEGRAM_BOT_TOKEN else os.getenv('TELEGRAM_BOT_TOKEN', '')
    inputs['earliest_date'] = EARLIEST_ACCEPTABLE_DATE
    inputs['latest_date'] = LATEST_ACCEPTABLE_DATE
    inputs['current_date'] = CURRENT_BOOKING_DATE
    inputs['check_interval'] = CHECK_INTERVAL
    
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


def main(gui_inputs: Optional[Dict[str, Any]] = None, stop_event: Optional[threading.Event] = None) -> None:
    """Main function to run the US Visa Appointment Bot.
    
    Args:
        gui_inputs: Optional dictionary of inputs from GUI. If provided, skips interactive prompts.
                   Expected keys: email, password, telegram_token, telegram_chat_id, location,
                   earliest_date, latest_date, current_date, check_interval
        stop_event: Optional threading.Event to signal when to stop the bot
    """
    logger.info("Starting US Visa Appointment Bot")
    
    # Initialize components
    state_manager = StateManager(STATE_FILE)
    telegram_bot = None
    scraper = None

    # Ensure stop_event exists for CLI runs too
    if stop_event is None:
        stop_event = threading.Event()

    use_telegram_inputs = (os.getenv("USE_TELEGRAM_INPUTS", "false").lower() == "true") and not gui_inputs
    
    try:
        # Initialize Telegram bot (needed for inputs and notifications)
        logger.info("Initializing Telegram bot...")
        def telegram_stop_callback() -> None:
            # Signal stop and close browser to interrupt any waits
            stop_event.set()
            try:
                if scraper:
                    scraper.close()
            except Exception as e:
                logger.warning(f"Error closing browser on stop: {e}")
            # Force-kill Chrome/Chromedriver to ensure full stop
            try:
                import subprocess
                subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], capture_output=True, shell=True)
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True, shell=True)
            except Exception as e:
                logger.warning(f"Error force-killing Chrome processes: {e}")

        if use_telegram_inputs:
            telegram_token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
            telegram_chat_id = TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "0")
            if not telegram_token:
                logger.error("Telegram bot token not set. Please set TELEGRAM_BOT_TOKEN in .env")
                sys.exit(1)
        else:
            # Get user inputs interactively or from GUI
            if gui_inputs:
                user_inputs = gui_inputs
                logger.info("Using inputs from GUI")
            else:
                user_inputs = get_user_inputs()
            telegram_token = user_inputs['telegram_token']
            telegram_chat_id = user_inputs['telegram_chat_id']

        chat_id = telegram_chat_id if telegram_chat_id and str(telegram_chat_id) != '0' else '0'
        telegram_bot = TelegramNotifier(telegram_token, chat_id, stop_callback=telegram_stop_callback)
        
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

        # If using Telegram inputs, ask for all configuration now
        if use_telegram_inputs:
            defaults = {
                "location": USER_CONSULATE,
                "earliest_date": EARLIEST_ACCEPTABLE_DATE,
                "latest_date": LATEST_ACCEPTABLE_DATE,
                "current_date": CURRENT_BOOKING_DATE,
                "check_interval": CHECK_INTERVAL,
            }
            user_inputs = get_inputs_via_telegram(telegram_bot, defaults)
            user_inputs["telegram_token"] = telegram_token
            user_inputs["telegram_chat_id"] = telegram_bot.chat_id

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
        
        # Parse date ranges from user inputs
        earliest_date_obj = datetime.strptime(earliest_date, "%Y-%m-%d").date()
        latest_date_obj = datetime.strptime(latest_date, "%Y-%m-%d").date()
        current_booking = datetime.strptime(current_booking_date, "%Y-%m-%d").date()

        # Use latest_date from user input as max_date
        max_date = latest_date

        def restart_session() -> VisaScraper:
            nonlocal scraper
            # Close existing browser if any
            if scraper:
                scraper.close()

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
            if existing_date:
                logger.info(f"Found existing appointment date: {existing_date}")

            # Set max_date in scraper
            scraper.set_max_date(max_date)

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
                telegram_bot.send_sync("❌ Failed to select location. Exiting.")
                sys.exit(1)

            # After selecting location, immediately check if calendar can be opened
            # System busy check should happen ONLY if calendar fails to open right after location selection
            logger.info("Location selected. Verifying calendar can be opened...")

            # Try to open calendar - if it fails, check for system busy
            calendar_test = scraper._open_calendar()
            if not calendar_test:
                logger.warning("Calendar failed to open right after location selection")
                # Only check for system busy if calendar fails to open
                if scraper.check_system_busy_error():
                    logger.error("System is busy. Please try again later.")
                    telegram_bot.send_sync("⚠️ <b>System is busy</b>\n\nPlease try again.")
                    logger.info("Exiting due to system busy error")
                    sys.exit(0)
                else:
                    logger.warning("Calendar failed to open but no system busy error detected. Will retry from home...")
            else:
                logger.info("Calendar opened successfully after location selection - system is ready")
                # Close the calendar for now, will reopen when checking dates
                try:
                    scraper.driver.find_element(By.ID, "appointments_consulate_appointment_date").click()
                except:
                    pass

            scraper.selected_counselor = selected_location
            scraper.counselor_selected = True

            return scraper

        # Start first session
        scraper = restart_session()
        
        selected_location = location
        telegram_bot.send_sync(
            f"✅ Monitoring appointments\n"
            f"📍 Location: {location}\n"
            f"📅 Date range: {earliest_date} to {latest_date}\n"
            f"📆 Current booking: {current_booking_date}\n"
            f"🔍 Looking for dates earlier than current booking..."
        )
        
        
        
        logger.info(f"Monitoring for location: {selected_location}, max date: {max_date}")
        logger.info(f"Will only book if date is earlier than: {current_booking_date}")
        
        # Main monitoring loop
        logger.info(f"Starting monitoring loop (checking every {check_interval} seconds)")
        check_count = 0
        
        # First check immediately (no wait) - subsequent checks will wait after retry
        first_check = True
        
        while True:
            # Check if stop was requested
            if stop_event and stop_event.is_set():
                logger.info("Stop signal received. Stopping bot...")
                telegram_bot.send_sync("🛑 Bot stopped by user")
                break
                
            try:
                check_count += 1

                # Restart session every 50 attempts
                if check_count >= 50:
                    telegram_bot.send_sync(
                        "🔁 <b>Restarting session</b>\n\n"
                        "Reached 50 attempts. Logging out and starting over..."
                    )
                    check_count = 0
                    scraper = restart_session()
                    continue
                logger.info(f"Check #{check_count}: Checking for available dates...")
                
                # Send Telegram notification for each attempt
                telegram_bot.send_sync(f"🔄 <b>Attempt #{check_count}</b>\n\nChecking for available dates...")
                
                # Check if stop was requested before proceeding
                if stop_event and stop_event.is_set():
                    logger.info("Stop signal received. Stopping bot...")
                    telegram_bot.send_sync("🛑 Bot stopped by user")
                    break
                
                # Ensure we're on the appointment page
                current_url = scraper.driver.current_url
                if '/appointment' not in current_url:
                    logger.info("Not on appointment page, navigating to reschedule...")
                    scraper.navigate_to_reschedule()
                    scraper.select_location(selected_location)
                
                # Check if stop was requested
                if stop_event and stop_event.is_set():
                    logger.info("Stop signal received. Stopping bot...")
                    telegram_bot.send_sync("🛑 Bot stopped by user")
                    break
                
                # Check for available dates (will attempt to open calendar first)
                # System busy check will only happen if calendar fails to open
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
                        # Clear stale date value and retry from home to avoid getting stuck
                        scraper.clear_date_field()
                        logger.info("Out-of-range date detected. Returning to home and retrying...")
                        telegram_bot.send_sync(
                            f"⏳ <b>Out-of-range date</b>\n\n"
                            f"Found {found_date_str} @ {found_location} (outside {earliest_date} to {latest_date}).\n"
                            f"Retrying from home..."
                        )
                        telegram_bot.send_sync("🔄 <b>No dates found</b>\n\nTrying again from home...")
                        try:
                            if scraper.go_to_home():
                                logger.info("Successfully navigated to home")
                                logger.info(f"Waiting {check_interval} seconds on home page before next check...")
                                for _ in range(check_interval):
                                    if stop_event and stop_event.is_set():
                                        logger.info("Stop signal received during wait. Stopping bot...")
                                        telegram_bot.send_sync("🛑 Bot stopped by user")
                                        break
                                    time.sleep(1)
                                if stop_event and stop_event.is_set():
                                    break
                                if scraper.click_continue():
                                    logger.info("Successfully clicked Continue")
                                    if scraper.navigate_to_reschedule():
                                        logger.info("Successfully navigated to reschedule")
                                        if scraper.select_location(selected_location):
                                            logger.info("Successfully selected location")
                                else:
                                    logger.warning("Failed to click Continue - will retry in next cycle")
                            else:
                                logger.warning("Failed to navigate to home - will retry in next cycle")
                        except Exception as e:
                            logger.error(f"Error during retry navigation: {e}", exc_info=True)
                            logger.info("Will retry navigation in next check cycle")
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
                        f"🎯 <b>Date found: {found_date_str} @ {found_location}</b>\n\n"
                        f"✅ Date: {found_date_str}\n"
                        f"📍 Location: {found_location}\n\n"
                        f"⏳ Trying to book the appointment now..."
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
                        if date_info.get('time_unavailable'):
                            logger.warning("Time dropdown not available. Returning to home and retrying...")
                            telegram_bot.send_sync(
                                f"⏳ <b>No time slots available</b>\n\n"
                                f"Found date {found_date_str} @ {found_location}, but time dropdown was empty.\n"
                                f"Retrying from home..."
                            )
                        else:
                            logger.error("Failed to book appointment")
                            telegram_bot.send_sync(
                                f"⚠️ <b>Booking Failed!</b>\n\n"
                                f"Slot was found on {found_date_str} @ {found_location}, but failed to book.\n"
                                f"Please check manually."
                            )
                        # Go back to home and retry
                        telegram_bot.send_sync("🔄 <b>No dates found</b>\n\nTrying again from home...")
                        scraper.go_to_home()
                        scraper.click_continue()
                        scraper.navigate_to_reschedule()
                        scraper.select_location(selected_location)
                else:
                    # Check if stop was requested
                    if stop_event and stop_event.is_set():
                        logger.info("Stop signal received. Stopping bot...")
                        telegram_bot.send_sync("🛑 Bot stopped by user")
                        break
                    
                    logger.info("No clickable dates found in calendar. Retrying from home...")
                    telegram_bot.send_sync("🔄 <b>No dates found</b>\n\nTrying again from home...")
                    
                    # Go back to home and retry (don't check for system busy here)
                    # System busy is only checked when calendar fails to open after location selection
                    # If calendar opened but no dates found, just retry
                    try:
                        if scraper.go_to_home():
                            logger.info("Successfully navigated to home")
                            
                            # Wait 30 seconds on home page before continuing
                            # Check for stop signal during wait
                            logger.info(f"Waiting {check_interval} seconds on home page before next check...")
                            for _ in range(check_interval):
                                if stop_event and stop_event.is_set():
                                    logger.info("Stop signal received during wait. Stopping bot...")
                                    telegram_bot.send_sync("🛑 Bot stopped by user")
                                    break
                                time.sleep(1)
                            
                            # Check again after wait
                            if stop_event and stop_event.is_set():
                                break
                            
                            # Check if stop was requested before continuing
                            if stop_event and stop_event.is_set():
                                logger.info("Stop signal received. Stopping bot...")
                                telegram_bot.send_sync("🛑 Bot stopped by user")
                                break
                            
                            # Now continue with the process (no more waits)
                            if scraper.click_continue():
                                logger.info("Successfully clicked Continue")
                                
                                # Check if stop was requested
                                if stop_event and stop_event.is_set():
                                    break
                                
                                if scraper.navigate_to_reschedule():
                                    logger.info("Successfully navigated to reschedule")
                                    
                                    # Check if stop was requested
                                    if stop_event and stop_event.is_set():
                                        break
                                    
                                    if scraper.select_location(selected_location):
                                        logger.info("Successfully selected location")
                                        
                                        # Check if stop was requested
                                        if stop_event and stop_event.is_set():
                                            break
                                        
                                        # After selecting location, verify calendar can still open
                                        # If calendar fails to open now, check for system busy
                                        if not scraper._open_calendar():
                                            logger.warning("Calendar failed to open after location selection in retry")
                                            if scraper.check_system_busy_error():
                                                logger.error("System is busy. Please try again later.")
                                                telegram_bot.send_sync("⚠️ <b>System is busy</b>\n\nPlease try again.")
                                                logger.info("Exiting due to system busy error")
                                                sys.exit(0)
                                            else:
                                                logger.warning("Calendar failed but no system busy - will continue retry")
                                        else:
                                            logger.info("Calendar opened successfully - ready for next check")
                                            # Close calendar for now
                                            try:
                                                scraper.driver.find_element(By.ID, "appointments_consulate_appointment_date").click()
                                            except:
                                                pass
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
                    
                    # Mark that first check is done (so subsequent retries will wait)
                    first_check = False
                    
                    # Check if stop was requested before continuing
                    if stop_event and stop_event.is_set():
                        logger.info("Stop signal received. Stopping bot...")
                        telegram_bot.send_sync("🛑 Bot stopped by user")
                        break
                    
                    continue  # Continue to next iteration of the while loop (will check dates immediately)
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                telegram_bot.send_sync("🛑 Bot stopped by user")
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
