"""Web scraping module for US visa appointment website."""
import logging
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from typing import Optional, Dict, List
from datetime import datetime, date
import json
import os

logger = logging.getLogger(__name__)


class VisaScraper:
    """Handles web scraping and automation for visa appointment website."""
    
    def __init__(self, email: str, password: str, url: str, headless: bool = False, browser_type: str = 'chrome', max_date: Optional[str] = None):
        """Initialize the scraper."""
        self.email = email
        self.password = password
        self.url = url
        self.headless = headless
        self.browser_type = browser_type
        self.driver: Optional[webdriver.Chrome] = None
        self.logged_in = False
        self.counselor_selected = False
        self.selected_counselor: Optional[str] = None
        self.max_date: Optional[date] = None
        if max_date:
            self.set_max_date(max_date)
    
    def _setup_driver(self):
        """Set up Selenium WebDriver."""
        try:
            if self.browser_type.lower() == 'chrome':
                chrome_options = Options()
                if self.headless:
                    chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            self.driver.maximize_window()
            logger.info("WebDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def set_max_date(self, max_date_str: str):
        """Set maximum date for checking appointments."""
        try:
            # Try various date formats
            date_formats = [
                '%Y-%m-%d',      # 2024-12-31
                '%m/%d/%Y',      # 12/31/2024
                '%d/%m/%Y',      # 31/12/2024
                '%Y/%m/%d',      # 2024/12/31
                '%m-%d-%Y',      # 12-31-2024
                '%d-%m-%Y',      # 31-12-2024
            ]
            
            for date_format in date_formats:
                try:
                    self.max_date = datetime.strptime(max_date_str, date_format).date()
                    logger.info(f"Maximum date set to: {self.max_date}")
                    return
                except ValueError:
                    continue
            
            raise ValueError(f"Could not parse date: {max_date_str}")
        except Exception as e:
            logger.error(f"Failed to set max date: {e}")
            self.max_date = None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string to a date object."""
        if not date_str:
            return None
        
        # Try various date formats
        date_formats = [
            '%Y-%m-%d',      # 2024-12-31
            '%m/%d/%Y',      # 12/31/2024
            '%d/%m/%Y',      # 31/12/2024
            '%Y/%m/%d',      # 2024/12/31
            '%m-%d-%Y',      # 12-31-2024
            '%d-%m-%Y',      # 31-12-2024
            '%B %d, %Y',     # December 31, 2024
            '%b %d, %Y',     # Dec 31, 2024
            '%d %B %Y',      # 31 December 2024
            '%d %b %Y',      # 31 Dec 2024
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format).date()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date string: {date_str}")
        return None
    
    def _is_date_within_range(self, appointment_date: str) -> bool:
        """Check if appointment date is within the specified range."""
        if not self.max_date:
            return True  # No max date set, accept all dates
        
        parsed_date = self._parse_date(appointment_date)
        if not parsed_date:
            # If we can't parse the date, assume it's valid (better to check than skip)
            logger.warning(f"Could not parse date '{appointment_date}', assuming valid")
            return True
        
        is_within_range = parsed_date <= self.max_date
        if not is_within_range:
            logger.info(f"Date {parsed_date} is after maximum date {self.max_date}, skipping")
        return is_within_range
    
    def login(self) -> bool:
        """Log in to the visa appointment website."""
        if not self.driver:
            if not self._setup_driver():
                return False
        
        try:
            logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)
            time.sleep(3)
            
            # Wait for email field and enter credentials
            wait = WebDriverWait(self.driver, 20)
            
            # Try to find email field (adjust selector based on actual website)
            email_selectors = [
                "input[type='email']",
                "input[name='user[email]']",
                "input[id*='email']",
                "input[placeholder*='email' i]",
                "#user_email",
                ".email",
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not email_field:
                logger.error("Could not find email field")
                return False
            
            email_field.clear()
            email_field.send_keys(self.email)
            logger.info("Entered email")
            time.sleep(1)
            
            # Find password field
            password_selectors = [
                "input[type='password']",
                "input[name='user[password]']",
                "input[id*='password']",
                "#user_password",
                ".password",
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            password_field.clear()
            password_field.send_keys(self.password)
            logger.info("Entered password")
            time.sleep(1)  # Wait after entering password
            
            # Find and click terms/conditions checkbox
            # Simple approach: find all checkboxes and click the first visible one
            logger.info("Looking for terms/conditions checkbox...")
            checkbox_found = False
            
            try:
                # Wait a moment for page to be ready
                time.sleep(0.5)
                
                # Try to find checkbox - simplest approach first
                all_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                logger.info(f"Found {len(all_checkboxes)} checkbox(es) on the page")
                
                for checkbox in all_checkboxes:
                    try:
                        # Check if visible
                        if checkbox.is_displayed():
                            logger.info(f"Found visible checkbox: id={checkbox.get_attribute('id')}, name={checkbox.get_attribute('name')}")
                            
                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                            time.sleep(0.3)
                            
                            # Check if already selected
                            if checkbox.is_selected():
                                logger.info("Checkbox already checked, skipping")
                                checkbox_found = True
                                break
                            
                            # Try regular click first
                            try:
                                checkbox.click()
                                logger.info("Clicked checkbox using regular click")
                                checkbox_found = True
                                time.sleep(0.3)
                                break
                            except Exception as e:
                                logger.debug(f"Regular click failed: {e}, trying JavaScript click")
                                # Try JavaScript click
                                self.driver.execute_script("arguments[0].click();", checkbox)
                                logger.info("Clicked checkbox using JavaScript click")
                                checkbox_found = True
                                time.sleep(0.3)
                                break
                    except Exception as e:
                        logger.debug(f"Error checking checkbox: {e}")
                        continue
                
                # If still not found, try finding via label
                if not checkbox_found:
                    logger.info("Trying to find checkbox via label...")
                    try:
                        # Find label containing "Privacy Policy" or "Terms"
                        label_xpath = "//label[contains(., 'Privacy Policy') or contains(., 'Terms of Use') or contains(., 'read and understood')]"
                        labels = self.driver.find_elements(By.XPATH, label_xpath)
                        
                        for label in labels:
                            try:
                                if label.is_displayed():
                                    # Try to find checkbox within label
                                    checkbox_in_label = label.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                                    if checkbox_in_label:
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox_in_label)
                                        time.sleep(0.3)
                                        
                                        if not checkbox_in_label.is_selected():
                                            try:
                                                checkbox_in_label.click()
                                            except:
                                                self.driver.execute_script("arguments[0].click();", checkbox_in_label)
                                            logger.info("Clicked checkbox found via label")
                                            checkbox_found = True
                                            time.sleep(0.3)
                                            break
                            except:
                                continue
                    except Exception as e:
                        logger.debug(f"Error finding checkbox via label: {e}")
                
            except Exception as e:
                logger.error(f"Error finding checkbox: {e}")
            
            if checkbox_found:
                logger.info("Checkbox clicked successfully")
                time.sleep(1)  # Wait after clicking checkbox before submitting
            else:
                logger.error("Terms/conditions checkbox not found - login will likely fail")
            
            # Find and click submit button
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='Sign' i]",
                ".btn-primary",
                "#sign_in",
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                logger.error("Could not find submit button")
                return False
            
            submit_button.click()
            logger.info("Clicked submit button")
            time.sleep(5)
            
            # Check if login was successful (look for dashboard or error message)
            current_url = self.driver.current_url
            if 'sign_in' not in current_url:
                self.logged_in = True
                logger.info("Login successful")
                return True
            else:
                # Check for error messages
                error_selectors = [
                    ".alert-danger",
                    ".error",
                    "[class*='error']",
                    ".flash-message",
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if error_element.is_displayed():
                            logger.error(f"Login failed: {error_element.text}")
                            return False
                    except NoSuchElementException:
                        continue
                
                logger.warning("Login status unclear - proceeding with caution")
                self.logged_in = True  # Assume success if no error found
                return True
                
        except Exception as e:
            logger.error(f"Login failed with exception: {e}")
            return False
    
    def get_existing_appointment_date(self) -> Optional[str]:
        """Extract existing appointment date from Groups page.
        
        Returns:
            Date string in format 'YYYY-MM-DD' or None if not found
        """
        try:
            wait = WebDriverWait(self.driver, 10)
            time.sleep(1)
            
            # Look for consular appointment text
            # Format: "21 June, 2027, 09:15 Toronto local time at Toronto"
            selectors = [
                "p.consular-appt",
                ".consular-appt",
            ]
            
            appointment_text = None
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        appointment_text = element.text
                        break
                except NoSuchElementException:
                    continue
            
            if not appointment_text:
                # Try XPath
                try:
                    xpath = "//p[contains(@class, 'consular-appt') or contains(text(), 'Consular Appointment')]"
                    element = self.driver.find_element(By.XPATH, xpath)
                    appointment_text = element.text
                except NoSuchElementException:
                    logger.warning("Could not find appointment date on page")
                    return None
            
            # Parse date from text like "21 June, 2027, 09:15 Toronto local time at Toronto"
            # Extract date part (before the comma with time)
            date_patterns = [
                r'(\d{1,2})\s+(\w+),\s+(\d{4})',  # "21 June, 2027"
                r'(\d{1,2})/(\d{1,2})/(\d{4})',   # "21/06/2027"
                r'(\d{4})-(\d{1,2})-(\d{1,2})',   # "2027-06-21"
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, appointment_text)
                if match:
                    if len(match.groups()) == 3:
                        if ',' in appointment_text:  # Format: "21 June, 2027"
                            day = match.group(1)
                            month_name = match.group(2)
                            year = match.group(3)
                            
                            # Convert month name to number
                            month_map = {
                                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                                'september': '09', 'october': '10', 'november': '11', 'december': '12',
                                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                            }
                            month = month_map.get(month_name.lower())
                            if month:
                                date_str = f"{year}-{month}-{day.zfill(2)}"
                                logger.info(f"Extracted appointment date: {date_str}")
                                return date_str
                        else:  # Numeric format
                            if '/' in appointment_text:  # MM/DD/YYYY or DD/MM/YYYY
                                # Try both formats
                                try:
                                    from datetime import datetime
                                    date_obj = datetime.strptime(f"{match.group(1)}/{match.group(2)}/{match.group(3)}", "%d/%m/%Y")
                                    date_str = date_obj.strftime("%Y-%m-%d")
                                    logger.info(f"Extracted appointment date: {date_str}")
                                    return date_str
                                except:
                                    try:
                                        date_obj = datetime.strptime(f"{match.group(1)}/{match.group(2)}/{match.group(3)}", "%m/%d/%Y")
                                        date_str = date_obj.strftime("%Y-%m-%d")
                                        logger.info(f"Extracted appointment date: {date_str}")
                                        return date_str
                                    except:
                                        pass
                            elif '-' in appointment_text:  # YYYY-MM-DD
                                date_str = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                                logger.info(f"Extracted appointment date: {date_str}")
                                return date_str
            
            logger.warning(f"Could not parse date from: {appointment_text}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting appointment date: {e}")
            return None
    
    def click_continue(self) -> bool:
        """Click Continue button after login."""
        if not self.logged_in:
            logger.error("Must be logged in to click Continue")
            return False
        
        try:
            wait = WebDriverWait(self.driver, 20)
            time.sleep(2)  # Wait for page to load
            
            # Find Continue button
            continue_selectors = [
                "a.button.primary[href*='continue_actions']",
                "a[href*='continue_actions']",
                "a.button[href*='continue']",
                ".button.primary",
                "a:contains('Continue')",
            ]
            
            continue_button = None
            for selector in continue_selectors:
                try:
                    continue_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not continue_button:
                # Try XPath
                try:
                    continue_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'continue_actions')]")))
                except TimeoutException:
                    logger.error("Could not find Continue button")
                    return False
            
            continue_button.click()
            logger.info("Clicked Continue button")
            time.sleep(2)  # Reduced from 3
            return True
            
        except Exception as e:
            logger.error(f"Failed to click Continue: {e}")
            return False
    
    def navigate_to_reschedule(self) -> bool:
        """Navigate to Reschedule Appointment page."""
        try:
            wait = WebDriverWait(self.driver, 20)
            time.sleep(2)
            
            # First, click the accordion title to expand "Reschedule Appointment" section
            logger.info("Looking for Reschedule Appointment accordion item...")
            
            # Find accordion item by looking for the title with "Reschedule Appointment" text
            accordion_title_xpath = "//a[@class='accordion-title' and contains(.//h5, 'Reschedule Appointment')]"
            
            try:
                accordion_title = wait.until(EC.element_to_be_clickable((By.XPATH, accordion_title_xpath)))
                logger.info("Found Reschedule Appointment accordion title, clicking to expand...")
                
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", accordion_title)
                time.sleep(0.5)
                
                # Click to expand accordion
                accordion_title.click()
                logger.info("Clicked accordion title to expand")
                time.sleep(2)  # Wait for accordion to expand
                
            except TimeoutException:
                logger.warning("Could not find accordion title, trying direct button...")
            
            # Now click the "Reschedule Appointment" button inside the expanded accordion
            logger.info("Looking for Reschedule Appointment button...")
            
            # Try multiple selectors for the button
            reschedule_button_selectors = [
                "a.button[href*='/appointment']:not([href*='continue'])",
                "a.button.primary[href*='appointment']",
                "a.button.small[href*='appointment']",
            ]
            
            reschedule_button = None
            for selector in reschedule_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and 'reschedule' in button.text.lower():
                            reschedule_button = button
                            break
                    if reschedule_button:
                        break
                except Exception:
                    continue
            
            # If not found with CSS, try XPath
            if not reschedule_button:
                try:
                    reschedule_button_xpath = "//a[contains(@href, '/appointment') and contains(@class, 'button') and contains(text(), 'Reschedule Appointment')]"
                    reschedule_button = wait.until(EC.element_to_be_clickable((By.XPATH, reschedule_button_xpath)))
                except TimeoutException:
                    # Try simpler XPath
                    try:
                        reschedule_button_xpath = "//a[@class='accordion-content']//a[contains(@href, '/appointment') and contains(@class, 'button')]"
                        reschedule_button = wait.until(EC.element_to_be_clickable((By.XPATH, reschedule_button_xpath)))
                    except TimeoutException:
                        logger.error("Could not find Reschedule Appointment button")
                        return False
            
            if reschedule_button:
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", reschedule_button)
                time.sleep(0.5)
                
                # Click the button
                reschedule_button.click()
                logger.info("Clicked Reschedule Appointment button")
                time.sleep(3)  # Wait for page to load
                return True
            else:
                logger.error("Could not find Reschedule Appointment button")
                return False
            
        except Exception as e:
            logger.error(f"Failed to navigate to reschedule: {e}")
            return False
    
    def check_system_busy_error(self) -> bool:
        """Check if system is busy error message is displayed.
        
        Returns:
            True if system is busy error is found, False otherwise
        """
        try:
            # Look for error message elements
            error_selectors = [
                (By.CLASS_NAME, "error"),
                (By.CLASS_NAME, "alert"),
                (By.CLASS_NAME, "alert-box"),
                (By.CSS_SELECTOR, ".error, .alert, .alert-box, [class*='error'], [class*='alert']"),
            ]
            
            for selector_type, selector_value in error_selectors:
                try:
                    error_elements = self.driver.find_elements(selector_type, selector_value)
                    for error_elem in error_elements:
                        if error_elem.is_displayed():
                            error_text = error_elem.text.lower()
                            busy_keywords = [
                                "system is busy",
                                "overloaded",
                                "temporarily unavailable",
                                "try again later",
                                "please try again later"
                            ]
                            if any(keyword in error_text for keyword in busy_keywords):
                                logger.warning(f"System is busy error detected: {error_elem.text}")
                                return True
                except:
                    continue
            
            # Also check page source for error messages
            try:
                page_text = self.driver.page_source.lower()
                busy_keywords = [
                    "system is busy",
                    "overloaded",
                    "temporarily unavailable",
                    "try again later",
                    "please try again later"
                ]
                if any(keyword in page_text for keyword in busy_keywords):
                    logger.warning("System is busy error detected in page source")
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            logger.debug(f"Error checking for system busy: {e}")
            return False
    
    def select_location(self, location: str = "Toronto") -> bool:
        """Select consular section location (e.g., Toronto)."""
        try:
            wait = WebDriverWait(self.driver, 20)
            time.sleep(2)
            
            # Find location dropdown using the specific ID from the HTML
            location_select = None
            try:
                location_select = wait.until(EC.presence_of_element_located((By.ID, "appointments_consulate_appointment_facility_id")))
                logger.info("Found location select dropdown")
            except TimeoutException:
                # Try fallback selectors
                location_selectors = [
                    "select[name*='facility_id']",
                    "select[name*='consular']",
                    "select[id*='facility']",
                    "select[name*='appointments[consulate_appointment][facility_id]']",
                ]
                for selector in location_selectors:
                    try:
                        location_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        logger.info(f"Found location select using selector: {selector}")
                        break
                    except TimeoutException:
                        continue
            
            if location_select:
                from selenium.webdriver.support.ui import Select
                select = Select(location_select)
                
                # Try to select by visible text
                try:
                    select.select_by_visible_text(location)
                    logger.info(f"Selected location: {location}")
                    time.sleep(2)  # Wait for page to update
                    
                    # Check for system busy error after selecting location
                    if self.check_system_busy_error():
                        logger.error("System is busy error detected after selecting location")
                        return False
                    
                    time.sleep(1)  # Additional wait for calendar to load
                    return True
                except:
                    # Try by value or partial text match
                    for option in select.options:
                        if location.lower() in option.text.lower():
                            select.select_by_visible_text(option.text)
                            logger.info(f"Selected location: {option.text}")
                            time.sleep(2)  # Wait for page to update
                            
                            # Check for system busy error after selecting location
                            if self.check_system_busy_error():
                                logger.error("System is busy error detected after selecting location")
                                return False
                            
                            time.sleep(1)  # Additional wait for calendar to load
                            return True
                
                logger.warning(f"Could not find location option: {location}")
                return False
            else:
                logger.warning("Location select not found, may already be selected")
                return True
            
        except Exception as e:
            logger.error(f"Failed to select location: {e}")
            return False
    
    def go_to_home(self) -> bool:
        """Navigate back to home page by directly navigating to the home URL."""
        try:
            wait = WebDriverWait(self.driver, 20)
            logger.info("Navigating to home page...")
            
            # Navigate directly to home URL (like referenced code)
            self.driver.get("https://ais.usvisa-info.com/en-ca/niv")
            
            # Wait for Continue button to appear (confirms we're on home page)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Continue')]")))
            logger.info("Successfully navigated to Candidate Home")
            time.sleep(1)
            return True
                
        except Exception as e:
            logger.error(f"Failed to navigate to home: {e}")
            return False
    
    def get_available_counselors(self) -> List[Dict[str, str]]:
        """Get list of available counselors/regions (legacy method)."""
        # Return empty list as we now use select_location instead
        return []
    
    def select_counselor(self, counselor_id: str) -> bool:
        """Select a counselor/region (legacy method, now uses select_location)."""
        # For backward compatibility, just call select_location
        return self.select_location(counselor_id)
    
    def _open_calendar(self) -> bool:
        """Open the calendar popup by clicking the calendar icon."""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for date field to be present
            date_field = wait.until(EC.presence_of_element_located((By.ID, "appointments_consulate_appointment_date")))
            
            # Find and click calendar icon
            calendar_icon_selectors = [
                ".calendar_icon",
                "img.calendar_icon",
                "img[src*='calendar']",
                "a[href='#select']",
            ]
            
            calendar_icon = None
            for selector in calendar_icon_selectors:
                try:
                    calendar_icon = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if calendar_icon.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            if not calendar_icon:
                logger.warning("Calendar icon not found")
                return False
            
            # Click calendar icon
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", calendar_icon)
                time.sleep(0.2)  # Reduced from 0.5
                calendar_icon.click()
                logger.info("Clicked calendar icon")
                time.sleep(0.8)  # Reduced from 2
                return True
            except Exception as e:
                logger.warning(f"Error clicking calendar icon: {e}")
                # Try JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", calendar_icon)
                    logger.info("Clicked calendar icon using JavaScript")
                    time.sleep(0.8)  # Reduced from 2
                    return True
                except Exception as e2:
                    logger.error(f"Failed to click calendar icon: {e2}")
                    return False
            
        except Exception as e:
            logger.error(f"Error opening calendar: {e}")
            return False
    
    def _click_next_month(self) -> bool:
        """Click the next month button in the calendar."""
        try:
            # Common selectors for next month button
            next_month_selectors = [
                ".ui-datepicker-next",
                ".datepicker-next",
                "a.ui-datepicker-next",
                "a[title='Next']",
                ".next",
                "a.next",
                "span.ui-icon-circle-triangle-e",
                ".yatri-datepicker-next",
            ]
            
            for selector in next_month_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(0.1)  # Reduced from 0.3
                            next_button.click()
                            logger.info("Clicked next month button")
                            time.sleep(0.8)  # Reduced from 1.5
                            return True
                        except Exception as e:
                            logger.debug(f"Error clicking next month with selector {selector}: {e}")
                            # Try JavaScript click
                            try:
                                self.driver.execute_script("arguments[0].click();", next_button)
                                logger.info("Clicked next month button using JavaScript")
                                time.sleep(0.8)  # Reduced from 1.5
                                return True
                            except:
                                continue
                except NoSuchElementException:
                    continue
            
            logger.warning("Next month button not found")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking next month: {e}")
            return False
    
    def _find_clickable_dates(self) -> List:
        """Find all clickable/available dates in the current calendar view."""
        clickable_dates = []
        try:
            # Wait for calendar to be visible (look for calendar popup/overlay)
            wait = WebDriverWait(self.driver, 5)
            
            # Common calendar popup selectors
            calendar_popup_selectors = [
                ".ui-datepicker",
                ".calendar-popup",
                ".datepicker",
                "[role='dialog']",
                ".yatri-datepicker",
            ]
            
            # Wait for calendar popup to appear
            calendar_popup = None
            for selector in calendar_popup_selectors:
                try:
                    calendar_popup = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if calendar_popup.is_displayed():
                        logger.info(f"Calendar popup found with selector: {selector}")
                        break
                except TimeoutException:
                    continue
            
            # Multiple strategies to find clickable dates
            date_selectors = [
                "td:not(.ui-state-disabled):not(.disabled) a",
                "td.available a",
                "td a:not(.ui-state-disabled)",
                "td a[href*='#']",
                "td:not([class*='disabled']) a",
                "a.ui-state-default:not(.ui-state-disabled)",
                "td:not([class*='unavailable']) a",
                "td a",
            ]
            
            for selector in date_selectors:
                try:
                    dates = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if dates:
                        # Filter to only visible and enabled dates
                        for date_element in dates:
                            try:
                                if date_element.is_displayed() and date_element.is_enabled():
                                    date_text = date_element.text.strip()
                                    if date_text and date_text.isdigit():  # Calendar days are usually just numbers
                                        clickable_dates.append(date_element)
                            except:
                                continue
                        
                        if clickable_dates:
                            logger.info(f"Found {len(clickable_dates)} clickable dates with selector: {selector}")
                            break
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            return clickable_dates
            
        except Exception as e:
            logger.error(f"Error finding clickable dates: {e}")
            return []
    
    def _traverse_calendar_for_clickable_date(self, max_months: int = 24) -> Optional:
        """Traverse calendar months until a clickable date is found."""
        try:
            months_checked = 0
            max_months_to_check = max_months
            
            while months_checked < max_months_to_check:
                # Look for clickable dates in current month
                clickable_dates = self._find_clickable_dates()
                
                if clickable_dates:
                    logger.info(f"Found {len(clickable_dates)} clickable dates in current month view")
                    # Return the first clickable date
                    return clickable_dates[0]
                
                # No clickable dates in current month, try next month
                logger.info(f"No clickable dates found in current month, clicking next month...")
                if not self._click_next_month():
                    logger.warning("Could not click next month button")
                    break
                
                months_checked += 1
                logger.info(f"Checked {months_checked} month(s), continuing...")
            
            if months_checked >= max_months_to_check:
                logger.warning(f"Checked {max_months_to_check} months, no clickable dates found")
            
            return None
            
        except Exception as e:
            logger.error(f"Error traversing calendar: {e}")
            return None
    
    def _select_date_in_calendar(self, date_element) -> bool:
        """Select a date element in the calendar."""
        try:
            if not date_element:
                return False
            
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", date_element)
            time.sleep(0.2)  # Reduced from 0.5
            
            # Click the date
            try:
                date_element.click()
            except:
                self.driver.execute_script("arguments[0].click();", date_element)
            
            date_text = date_element.text.strip()
            logger.info(f"Selected date: {date_text}")
            time.sleep(1.5)  # Reduced from 2 - Wait for date to be selected and calendar to close
            return True
            
        except Exception as e:
            logger.error(f"Error clicking date: {e}")
            return False
    
    def check_available_dates(self) -> Optional[Dict[str, str]]:
        """Check for available appointment dates."""
        if not self.logged_in:
            logger.error("Must be logged in to check dates")
            return None
        
        try:
            wait = WebDriverWait(self.driver, 20)
            time.sleep(2)
            
            # Wait for date/time fields to appear after location selection
            try:
                date_field = wait.until(EC.presence_of_element_located((By.ID, "appointments_consulate_appointment_date")))
                logger.info("Date field found, checking calendar...")
            except TimeoutException:
                logger.warning("Date field not found - calendar may not be loaded")
                return None
            
            # Check if date field already has a value
            date_field_value = date_field.get_attribute('value')
            if date_field_value and date_field_value.strip():
                logger.info(f"Date field already has a value: {date_field_value}")
                # Date is already selected, return it
                location = self.selected_counselor or "Toronto"
                return {
                    'date': date_field_value,
                    'location': location,
                    'element': None
                }
            
            # Check for system busy error before trying to open calendar
            if self.check_system_busy_error():
                logger.error("System is busy error detected - cannot open calendar")
                return None
            
            # Open calendar
            if not self._open_calendar():
                logger.warning("Failed to open calendar")
                # Check again for system busy error
                if self.check_system_busy_error():
                    logger.error("System is busy error detected after failed calendar open")
                return None
            
            # Traverse calendar months to find a clickable date
            # Limit to 24 months ahead (2 years) or until max_date if set
            max_months = 24
            if self.max_date:
                # Calculate months until max_date
                months_until_max = (self.max_date.year - date.today().year) * 12 + (self.max_date.month - date.today().month)
                if months_until_max > 0:
                    max_months = min(months_until_max + 1, 24)  # Add 1 to include the month itself
            
            logger.info(f"Traversing calendar (up to {max_months} months) to find clickable date...")
            selected_date_element = self._traverse_calendar_for_clickable_date(max_months=max_months)
            
            if not selected_date_element:
                logger.warning("No clickable dates found after traversing calendar")
                return None
            
            # Click the selected date
            if self._select_date_in_calendar(selected_date_element):
                # Wait for date selection and calendar to close
                time.sleep(1)  # Reduced from 2
                
                # Check the date field value after selection
                date_field_value = date_field.get_attribute('value')
                location = self.selected_counselor or "Toronto"
                
                return {
                    'date': date_field_value or selected_date_element.text,
                    'location': location,
                    'element': selected_date_element
                }
            else:
                logger.error("Failed to select date in calendar")
                return None
            
        except Exception as e:
            logger.error(f"Error checking available dates: {e}")
            return None
    
    def get_available_times(self) -> List[str]:
        """Get list of available times from the time dropdown."""
        available_times = []
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for time dropdown to be populated (it loads after date selection)
            time_select = None
            time_selectors = [
                "select#appointments_consulate_appointment_time",
                "select[name*='time']",
                "select[id*='time']",
                ".time-select select",
                "select.time-slot",
            ]
            
            for selector in time_selectors:
                try:
                    time_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if time_select.is_displayed():
                        break
                except TimeoutException:
                    continue
            
            if not time_select:
                logger.warning("Time select dropdown not found")
                return []
            
            # Wait for options to be populated (may take a moment after date selection)
            max_wait = 5  # Reduced from 10
            waited = 0
            while waited < max_wait:
                from selenium.webdriver.support.ui import Select
                select = Select(time_select)
                options = select.options
                
                # Check if we have more than just the empty option
                if len(options) > 1:
                    for option in options:
                        option_text = option.text.strip()
                        if option_text and option.is_enabled() and option.get_attribute('value'):
                            available_times.append(option_text)
                    
                    if available_times:
                        logger.info(f"Found {len(available_times)} available times")
                        return available_times
                
                time.sleep(0.3)  # Reduced from 0.5
                waited += 0.3
            
            logger.warning("No available times found in dropdown")
            return []
            
        except Exception as e:
            logger.error(f"Error getting available times: {e}")
            return []
    
    def select_time_and_reschedule(self, date_info: Dict[str, str], preferred_time: Optional[str] = None) -> bool:
        """Select time and click Reschedule button.
        
        Args:
            date_info: Dictionary containing date information
            preferred_time: Preferred time slot (e.g., "07:30", "08:00"). 
                          If None or not available, selects first available time.
        """
        try:
            wait = WebDriverWait(self.driver, 20)
            
            # Ensure date is selected first (click on date element if provided)
            if 'element' in date_info and date_info['element']:
                try:
                    date_element = date_info['element']
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", date_element)
                    time.sleep(0.2)  # Reduced from 0.5
                    date_element.click()
                    logger.info("Clicked on date")
                    time.sleep(2)  # Reduced from 3 - Wait for time dropdown to populate
                except Exception as e:
                    logger.warning(f"Could not click date element: {e}")
            
            # Wait for time dropdown to be populated after date selection
            time_select = None
            time_selectors = [
                "select#appointments_consulate_appointment_time",
                "select[name*='time']",
                "select[id*='time']",
                ".time-select select",
                "select.time-slot",
            ]
            
            # Wait for time dropdown to appear and be populated
            for selector in time_selectors:
                try:
                    time_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if time_select.is_displayed():
                        # Wait for options to be populated (reduced from 10 to 5 seconds)
                        max_wait = 5
                        waited = 0
                        while waited < max_wait:
                            from selenium.webdriver.support.ui import Select
                            select = Select(time_select)
                            options = select.options
                            # Check if we have more than just the empty option
                            if len(options) > 1:
                                break
                            time.sleep(0.3)  # Reduced from 0.5
                            waited += 0.3
                        break
                except TimeoutException:
                    continue
            
            if not time_select:
                logger.error("Could not find time selector")
                return False
            
            # Select time
            from selenium.webdriver.support.ui import Select
            select = Select(time_select)
            time_selected = False
            
            if preferred_time:
                # Try to select preferred time
                logger.info(f"Attempting to select preferred time: {preferred_time}")
                # Normalize preferred time (remove spaces, handle various formats)
                preferred_normalized = preferred_time.strip().replace(' ', '')
                
                for option in select.options:
                    option_text = option.text.strip()
                    option_value = option.get_attribute('value')
                    
                    if not option_text or not option_value:
                        continue
                    
                    # Normalize option text for comparison
                    option_normalized = option_text.replace(' ', '')
                    
                    # Try exact match first
                    if option_normalized == preferred_normalized or option_text == preferred_time:
                        if option.is_enabled():
                            try:
                                select.select_by_visible_text(option_text)
                                logger.info(f"Selected preferred time: {option_text}")
                                time_selected = True
                                time.sleep(0.5)  # Reduced from 1
                                break
                            except Exception as e:
                                logger.warning(f"Could not select preferred time {option_text}: {e}")
                                continue
                    
                    # Try partial match (e.g., "7:30" matches "07:30")
                    if preferred_normalized.replace('0', '') in option_normalized.replace('0', '') or \
                       option_normalized.replace('0', '') in preferred_normalized.replace('0', ''):
                        if option.is_enabled():
                            try:
                                select.select_by_visible_text(option_text)
                                logger.info(f"Selected time (partial match): {option_text} (preferred: {preferred_time})")
                                time_selected = True
                                time.sleep(0.5)  # Reduced from 1
                                break
                            except Exception as e:
                                logger.warning(f"Could not select time {option_text}: {e}")
                                continue
                
                if not time_selected:
                    logger.warning(f"Preferred time '{preferred_time}' not available, selecting first available time")
            
            # If preferred time not selected, select first available time
            if not time_selected:
                for option in select.options:
                    option_text = option.text.strip()
                    option_value = option.get_attribute('value')
                    if option_text and option_value and option.is_enabled():
                        try:
                            select.select_by_visible_text(option_text)
                            logger.info(f"Selected first available time: {option_text}")
                            time_selected = True
                            time.sleep(0.5)  # Reduced from 1
                            break
                        except Exception as e:
                            logger.warning(f"Could not select time {option_text}: {e}")
                            continue
            
            if not time_selected:
                logger.error("Could not select any time from dropdown")
                return False
            
            # Wait a moment for the form to update and enable the Reschedule button
            time.sleep(0.5)  # Reduced from 1
            
            # Check if Reschedule button is enabled
            reschedule_button = None
            reschedule_selectors = [
                "input#appointments_submit",
                "input[value*='Reschedule' i]",
                "button[value*='Reschedule' i]",
                "input[type='submit']",
            ]
            
            for selector in reschedule_selectors:
                try:
                    reschedule_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if reschedule_button.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            if not reschedule_button:
                logger.error("Could not find Reschedule button")
                return False
            
            # Wait for button to be enabled (it's disabled until time is selected)
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#appointments_submit")))
                logger.info("Reschedule button is enabled")
            except TimeoutException:
                logger.warning("Reschedule button not enabled after time selection, checking if it's clickable...")
                # Check if button exists and try to enable it
                try:
                    # Sometimes the button needs a small delay
                    time.sleep(0.5)
                    if reschedule_button.is_enabled():
                        logger.info("Reschedule button is now enabled")
                    else:
                        logger.warning("Reschedule button is still disabled, attempting to click anyway...")
                except:
                    pass
            
            # Check if button has data-confirm attribute (triggers JavaScript confirmation)
            has_data_confirm = False
            try:
                data_confirm = reschedule_button.get_attribute('data-confirm')
                if data_confirm:
                    logger.info(f"Reschedule button has data-confirm attribute: {data_confirm}")
                    has_data_confirm = True
                    # This will trigger a Foundation reveal modal when clicked
            except:
                pass
            
            # Click Reschedule button
            try:
                # Scroll into view first
                self.driver.execute_script("arguments[0].scrollIntoView(true);", reschedule_button)
                time.sleep(0.1)
                
                # Try regular click
                reschedule_button.click()
                logger.info("Clicked Reschedule button")
                
                # Immediately handle confirmation dialog/modal (no wait, especially for data-confirm)
                if has_data_confirm:
                    # For data-confirm, wait a tiny bit for Foundation reveal modal to appear
                    time.sleep(0.2)
                
                confirmation_handled = self._handle_reschedule_confirmation()
                
                if not confirmation_handled:
                    logger.warning("Could not find confirmation dialog, trying alternative methods...")
                    # Try to find and click confirm button directly
                    try:
                        # Look for any button with "Confirm" text that's visible
                        confirm_buttons = self.driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]")
                        for btn in confirm_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                logger.info("Found Confirm button via direct search")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                time.sleep(0.2)
                                btn.click()
                                logger.info("Clicked Confirm button")
                                confirmation_handled = True
                                time.sleep(1)
                                break
                    except Exception as e:
                        logger.warning(f"Alternative confirmation method failed: {e}")
                
                # Wait for page to navigate or form to submit after confirmation
                time.sleep(1.5)  # Reduced further for faster processing
                
                # Verify booking was successful by checking URL or page content
                current_url = self.driver.current_url
                logger.info(f"Current URL after confirmation: {current_url}")
                
                # Check for success indicators first (instructions page is SUCCESS)
                if '/appointment/instructions' in current_url or 'instructions' in current_url.lower():
                    logger.info("✅ Booking successful - navigated to instructions page")
                    return True
                
                if '/groups' in current_url or '/account' in current_url:
                    logger.info("✅ Booking successful - navigated to groups/account page")
                    return True
                
                # Check if still on appointment scheduling page (not instructions) - this means failure
                if '/appointment' in current_url and '/instructions' not in current_url:
                    logger.warning("Still on appointment scheduling page - booking likely failed")
                    # Check for error messages
                    try:
                        page_text = self.driver.page_source.lower()
                        error_indicators = [
                            r"error",
                            r"failed",
                            r"try again",
                            r"system is busy",
                        ]
                        for indicator in error_indicators:
                            if re.search(indicator, page_text):
                                logger.warning(f"Found error indicator: {indicator}")
                                return False
                    except:
                        pass
                    return False
                else:
                    # We navigated away from appointment scheduling page - check for success
                    logger.info("Navigated away from appointment page - checking for success...")
                    try:
                        # Check page content for success indicators
                        page_text = self.driver.page_source.lower()
                        success_indicators = [
                            r"instructions",
                            r"step.*5",
                            r"appointment.*rescheduled.*success",
                            r"your appointment has been",
                        ]
                        for indicator in success_indicators:
                            if re.search(indicator, page_text):
                                logger.info(f"Found success indicator: {indicator}")
                                return True
                        
                        logger.info("Navigated to different page - assuming success")
                        return True
                    except Exception as e:
                        logger.warning(f"Error checking success indicators: {e}")
                        # If we navigated away, assume success
                        return True
                    
            except Exception as e:
                logger.error(f"Failed to click Reschedule button: {e}")
                # Try JavaScript click as fallback
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", reschedule_button)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", reschedule_button)
                    logger.info("Clicked Reschedule button using JavaScript")
                    time.sleep(1)
                    
                    # Handle confirmation dialog
                    confirmation_handled = self._handle_reschedule_confirmation()
                    if not confirmation_handled:
                        logger.warning("Could not find confirmation dialog (JavaScript click), proceeding anyway...")
                    
                    time.sleep(2)
                    
                    # Verify booking
                    current_url = self.driver.current_url
                    if '/appointment' not in current_url or 'instructions' in current_url.lower():
                        logger.info("Booking appears successful (JavaScript click)")
                        return True
                    return True  # Assume success
                except Exception as e2:
                    logger.error(f"Failed to click Reschedule button with JavaScript: {e2}")
                    # Even if click failed, try to handle confirmation if modal appeared
                    try:
                        time.sleep(1)
                        self._handle_reschedule_confirmation()
                    except:
                        pass
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to reschedule appointment: {e}")
            return False
    
    def _handle_reschedule_confirmation(self) -> bool:
        """Handle the confirmation dialog that appears after clicking Reschedule button.
        
        Returns:
            True if confirmation was handled, False otherwise
        """
        try:
            wait = WebDriverWait(self.driver, 3)  # Reduced wait time
            
            # Try to handle JavaScript alert/confirm dialog first (immediate, no wait)
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                logger.info(f"Found JavaScript alert: {alert_text}")
                # Accept the alert (click OK/Confirm) immediately
                alert.accept()
                logger.info("✅ Accepted JavaScript alert/confirmation")
                time.sleep(0.1)
                return True
            except:
                # No JavaScript alert, try modal dialog
                pass
            
            # Try to find Foundation reveal modal immediately (data-confirm uses this)
            # Don't wait - try immediately
            try:
                # Look for Foundation reveal modal that appears instantly
                reveal_modal = self.driver.find_element(By.CSS_SELECTOR, ".reveal-modal, .reveal")
                if reveal_modal.is_displayed():
                    logger.info("Found Foundation reveal modal, looking for Confirm button...")
                    # Find Confirm button in the modal
                    confirm_btn = reveal_modal.find_element(By.XPATH, ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')] | .//button[contains(@class, 'primary')] | .//a[contains(@class, 'button') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]")
                    if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                        logger.info("Found Confirm button in reveal modal")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", confirm_btn)
                        time.sleep(0.1)
                        confirm_btn.click()
                        logger.info("✅ Clicked Confirm button in reveal modal")
                        time.sleep(0.2)
                        return True
            except:
                pass
            
            # Small wait for modal to appear if not found immediately
            time.sleep(0.2)
            
            # Look for modal confirmation dialog - use valid CSS selectors only
            # Foundation reveal modals typically have these structures
            confirmation_selectors = [
                # Foundation reveal modal buttons (most common)
                ".reveal-modal button.primary",
                ".reveal button.primary",
                ".reveal button.button.primary",
                ".reveal-modal .button.primary",
                # Buttons in reveal that aren't close buttons
                ".reveal button[type='button']:not(.close-button)",
                ".reveal-modal button[type='button']:not(.close-button)",
                # Generic modal buttons
                ".modal button.btn-primary",
                ".modal-dialog button.btn-primary",
                ".modal-content button.btn-primary",
                # Button with confirm class or id
                "button.confirm",
                "#confirm-button",
                ".confirm-button",
            ]
            
            for selector in confirmation_selectors:
                try:
                    # Try to find button immediately (reduced timeout)
                    confirmation_button = WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    if confirmation_button.is_displayed():
                        logger.info(f"Found confirmation button with selector: {selector}")
                        # Scroll into view and click immediately
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", confirmation_button)
                        time.sleep(0.05)
                        confirmation_button.click()
                        logger.info("✅ Clicked confirmation button")
                        time.sleep(0.2)
                        return True
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Try XPath for confirmation buttons (more reliable for text matching)
            xpath_selectors = [
                # Look for button with "Confirm" text in visible modals
                "//div[contains(@class, 'reveal') or contains(@class, 'modal')]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]",
                "//div[contains(@class, 'reveal') or contains(@class, 'modal')]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm') and not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cancel'))]",
                # Look in reveal modal specifically
                "//div[@class='reveal-modal']//button[contains(@class, 'primary')]",
                "//div[contains(@class, 'reveal')]//button[contains(@class, 'primary')]",
                # Generic button with Confirm text
                "//button[normalize-space(text())='Confirm']",
                "//button[normalize-space(text())='OK']",
            ]
            
            for xpath in xpath_selectors:
                try:
                    # Try to find button immediately (reduced timeout)
                    confirmation_button = WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    if confirmation_button.is_displayed() and confirmation_button.is_enabled():
                        logger.info(f"Found confirmation button with XPath: {xpath}")
                        # Scroll into view and click immediately
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", confirmation_button)
                        time.sleep(0.05)
                        confirmation_button.click()
                        logger.info("✅ Clicked confirmation button (XPath)")
                        time.sleep(0.2)
                        return True
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Check if there's a modal that needs to be closed/confirmed
            try:
                # Look for any visible modal/reveal
                modals = self.driver.find_elements(By.CSS_SELECTOR, ".reveal-modal, .reveal, .modal, [role='dialog'], [class*='reveal'], [class*='modal']")
                for modal in modals:
                    try:
                        if modal.is_displayed():
                            logger.info("Found visible modal, searching for Confirm button...")
                            # Try to find buttons in the modal
                            buttons = modal.find_elements(By.CSS_SELECTOR, "button, a.button")
                            for button in buttons:
                                try:
                                    button_text = button.text.strip().lower()
                                    if button.is_displayed() and button.is_enabled():
                                        # Look for confirm/ok buttons (exclude cancel/close)
                                        if any(word in button_text for word in ['confirm', 'ok']) and \
                                           not any(word in button_text for word in ['cancel', 'close']):
                                            logger.info(f"Found confirmation button in modal: {button_text}")
                                            # Scroll into view and click immediately
                                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                            time.sleep(0.1)
                                            button.click()
                                            logger.info("Clicked confirmation button in modal")
                                            time.sleep(0.3)
                                            return True
                                except:
                                    continue
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Error searching modals: {e}")
            
            logger.warning("Could not find confirmation dialog/button")
            return False
            
        except Exception as e:
            logger.error(f"Error handling confirmation dialog: {e}")
            return False
            
            # Click Reschedule button
            reschedule_selectors = [
                "input[value*='Reschedule' i]",
                "button[value*='Reschedule' i]",
                "button:contains('Reschedule')",
                ".reschedule-button",
                "button[type='submit']",
                "input[type='submit']",
            ]
            
            for selector in reschedule_selectors:
                try:
                    reschedule_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    reschedule_button.click()
                    logger.info("Clicked Reschedule button")
                    time.sleep(3)
                    return True
                except (NoSuchElementException, TimeoutException):
                    continue
            
            # Try XPath
            try:
                reschedule_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Reschedule'] | //button[contains(text(), 'Reschedule')]")))
                reschedule_button.click()
                logger.info("Clicked Reschedule button (via XPath)")
                time.sleep(3)
                return True
            except TimeoutException:
                logger.error("Could not find Reschedule button")
                return False
            
        except Exception as e:
            logger.error(f"Failed to reschedule appointment: {e}")
            return False
    
    def book_appointment(self, date_info: Dict[str, str], preferred_time: Optional[str] = None) -> bool:
        """Book/reschedule an appointment for the given date (uses select_time_and_reschedule).
        
        Args:
            date_info: Dictionary containing date information
            preferred_time: Preferred time slot (e.g., "07:30", "08:00"). 
                          If None or not available, selects first available time.
        """
        return self.select_time_and_reschedule(date_info, preferred_time)
    
    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
