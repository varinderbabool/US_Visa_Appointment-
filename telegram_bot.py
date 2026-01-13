"""Telegram bot module for notifications and confirmations."""
import logging
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError, BadRequest
from typing import Optional, Callable
import threading
import queue

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Handles Telegram notifications and confirmation requests."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram bot."""
        self.bot_token = bot_token
        self.chat_id = str(chat_id)  # Ensure string type
        self.bot = Bot(token=bot_token)
        self.confirmation_callback: Optional[Callable[[bool], None]] = None
        self.pending_confirmation: bool = False
        self.pending_time_selection: bool = False
        self.confirmation_queue = queue.Queue()
        self.time_queue = queue.Queue()
        self.app = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._setup_bot()
    
    def _setup_bot(self):
        """Set up the Telegram bot application in a separate thread."""
        def run_bot():
            """Run the bot in a separate event loop."""
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            self.app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self._start_command))
            self.app.add_handler(CommandHandler("status", self._status_command))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            # Run bot
            self._loop.run_until_complete(self.app.initialize())
            self._loop.run_until_complete(self.app.start())
            self._loop.run_until_complete(self.app.updater.start_polling())
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_bot, daemon=True)
        self._thread.start()
        # Give bot time to initialize
        import time
        time.sleep(2)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        # Store chat ID if it matches
        incoming_chat_id = str(update.message.chat_id)
        if incoming_chat_id != self.chat_id:
            logger.info(f"Received message from chat ID: {incoming_chat_id} (current: {self.chat_id})")
            # If chat_id was empty/placeholder, update it
            if not self.chat_id or self.chat_id == '0' or self.chat_id == '':
                self.chat_id = incoming_chat_id
                logger.info(f"Updated chat ID to: {self.chat_id}")
        
        await update.message.reply_text(
            "👋 US Visa Appointment Bot is running!\n\n"
            "I will notify you when appointment dates become available.\n"
            "Use /status to check the current status."
        )
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        status_msg = "✅ Bot is active and monitoring for appointments."
        if self.pending_confirmation:
            status_msg += "\n⏳ Waiting for your confirmation on an available date."
        await update.message.reply_text(status_msg)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages."""
        incoming_chat_id = str(update.message.chat_id)
        
        # If chat_id was empty/placeholder, update it with the first message
        if not self.chat_id or self.chat_id == '0' or self.chat_id == '':
            self.chat_id = incoming_chat_id
            logger.info(f"Auto-detected chat ID: {self.chat_id}")
        
        if incoming_chat_id != self.chat_id:
            return
        
        text = update.message.text.strip()
        text_lower = text.lower()
        
        if self.pending_time_selection:
            # User is providing preferred time
            if text_lower in ['skip', 'any', 'first', 'auto']:
                self.pending_time_selection = False
                self.time_queue.put(None)
                await update.message.reply_text("✅ Will select first available time.")
            else:
                # Treat as time input
                self.pending_time_selection = False
                self.time_queue.put(text)
                await update.message.reply_text(f"✅ Preferred time set to: {text}")
        elif self.pending_confirmation:
            if text_lower in ['yes', 'y', 'confirm', 'ok', 'book']:
                self.pending_confirmation = False
                self.confirmation_queue.put(True)
                await update.message.reply_text("✅ Confirmed! Booking the appointment...")
            elif text_lower in ['no', 'n', 'cancel', 'skip']:
                self.pending_confirmation = False
                self.confirmation_queue.put(False)
                await update.message.reply_text("❌ Cancelled. Will continue checking for other dates.")
            else:
                await update.message.reply_text(
                    "Please reply with 'yes' to confirm or 'no' to cancel."
                )
    
    async def send_notification(self, message: str):
        """Send a notification message."""
        # Don't send if chat_id is not set yet
        if not self.chat_id or self.chat_id == '0' or self.chat_id == '':
            logger.warning(f"Cannot send notification - chat_id not set yet. Message: {message[:50]}...")
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Sent Telegram notification: {message[:50]}...")
        except BadRequest as e:
            error_msg = str(e)
            if "chat not found" in error_msg.lower() or "chat_id is empty" in error_msg.lower():
                logger.error(f"Chat not found - invalid chat_id: {self.chat_id}. Please send /start to your bot first.")
                # Reset chat_id so it can be detected again
                self.chat_id = '0'
            else:
                logger.error(f"Telegram BadRequest error: {e}")
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    async def request_confirmation(self, date_info: str) -> bool:
        """Request confirmation from user and wait for response."""
        self.pending_confirmation = True
        
        message = (
            "📅 <b>Appointment Date Available!</b>\n\n"
            f"{date_info}\n\n"
            "Reply with <b>yes</b> to book this appointment or <b>no</b> to skip."
        )
        
        await self.send_notification(message)
        
        # Wait for confirmation (timeout after 5 minutes)
        try:
            confirmation = self.confirmation_queue.get(timeout=300)
            return confirmation
        except queue.Empty:
            self.pending_confirmation = False
            logger.warning("Confirmation timeout - no response received")
            await self.send_notification("⏱️ Confirmation timeout. Continuing to check for other dates.")
            return False
    
    async def request_preferred_time(self, available_times: list) -> Optional[str]:
        """Request preferred time from user and wait for response.
        
        Args:
            available_times: List of available time slots
            
        Returns:
            Preferred time string or None if user wants first available
        """
        self.pending_time_selection = True
        
        if available_times:
            times_list = "\n".join([f"  • {t}" for t in available_times])
            message = (
                "⏰ <b>Select Preferred Time</b>\n\n"
                f"Available times:\n{times_list}\n\n"
                "Reply with your preferred time (e.g., <b>07:30</b> or <b>08:00</b>)\n"
                "Or reply <b>skip</b> to select first available time."
            )
        else:
            message = (
                "⏰ <b>Select Preferred Time</b>\n\n"
                "Reply with your preferred time (e.g., <b>07:30</b> or <b>08:00</b>)\n"
                "Or reply <b>skip</b> to select first available time."
            )
        
        await self.send_notification(message)
        
        # Wait for time selection (timeout after 2 minutes)
        try:
            preferred_time = self.time_queue.get(timeout=120)
            return preferred_time
        except queue.Empty:
            self.pending_time_selection = False
            logger.warning("Time selection timeout - will use first available")
            await self.send_notification("⏱️ Time selection timeout. Will select first available time.")
            return None
    
    def send_sync(self, message: str):
        """Synchronous wrapper for sending messages."""
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.send_notification(message), self._loop)
            future.result(timeout=30)
        else:
            asyncio.run(self.send_notification(message))
    
    def request_confirmation_sync(self, date_info: str) -> bool:
        """Synchronous wrapper for requesting confirmation."""
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.request_confirmation(date_info), self._loop)
            return future.result(timeout=300)
        else:
            return asyncio.run(self.request_confirmation(date_info))
    
    def request_preferred_time_sync(self, available_times: list) -> Optional[str]:
        """Synchronous wrapper for requesting preferred time."""
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.request_preferred_time(available_times), self._loop)
            return future.result(timeout=120)
        else:
            return asyncio.run(self.request_preferred_time(available_times))
    
    def stop(self):
        """Stop the bot."""
        if self.app and self._loop:
            asyncio.run_coroutine_threadsafe(self.app.stop(), self._loop)
            asyncio.run_coroutine_threadsafe(self.app.shutdown(), self._loop)
            self._loop.call_soon_threadsafe(self._loop.stop)
