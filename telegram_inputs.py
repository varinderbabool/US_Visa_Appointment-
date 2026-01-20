"""Telegram-based input collection for bot configuration."""
from datetime import datetime
from typing import Dict, Any, Optional

from settings import CONSULATES


def get_inputs_via_telegram(
    telegram_bot,
    defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """Collect required inputs via Telegram messages."""

    def ask(
        prompt: str,
        default: Optional[str] = None,
        required: bool = False,
        validator=None,
        error_msg: str = "Invalid input. Please try again."
    ) -> str:
        for _ in range(3):
            value = telegram_bot.request_input_sync(prompt, timeout=300).strip()
            if not value:
                if default is not None:
                    return str(default)
                if required:
                    telegram_bot.send_sync(error_msg)
                    continue
                return ""
            if validator and not validator(value):
                telegram_bot.send_sync(error_msg)
                continue
            return value
        raise ValueError("Too many invalid inputs.")

    def is_valid_email(value: str) -> bool:
        return "@" in value and "." in value.split("@")[-1]

    def is_valid_date(value: str) -> bool:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def is_valid_interval(value: str) -> bool:
        try:
            return int(value) > 0
        except ValueError:
            return False

    telegram_bot.send_sync(
        "📝 <b>Telegram setup</b>\n\n"
        "Please provide the following details.\n"
        "Dates must be in <b>YYYY-MM-DD</b> format.\n"
        "You can reply with <b>skip</b> only where a default is provided."
    )

    email = ask(
        "📧 <b>Email:</b>\nPlease enter your visa account email.",
        required=True,
        validator=is_valid_email,
        error_msg="❌ Invalid email. Please enter a valid email address."
    )

    password = ask(
        "🔑 <b>Password:</b>\nPlease enter your visa account password.",
        required=True,
        error_msg="❌ Password cannot be empty."
    )

    location_prompt = (
        "📍 <b>Location 1:</b>\n"
        f"Available: {', '.join(CONSULATES.keys())}\n"
        f"Default: {defaults['location']}\n"
        "Reply with a city name or leave empty to use default."
    )
    location_input = ask(location_prompt, default=defaults["location"])
    location = defaults["location"]
    for key in CONSULATES.keys():
        if key.lower() == location_input.strip().lower():
            location = key
            break

    location2_prompt = (
        "📍 <b>Location 2 (optional):</b>\n"
        f"Available: {', '.join(CONSULATES.keys())}\n"
        "Reply with a city name or leave empty to skip."
    )
    location2_input = ask(location2_prompt, default=defaults.get("location2", ""))
    location2 = ""
    for key in CONSULATES.keys():
        if key.lower() == location2_input.strip().lower():
            location2 = key
            break

    earliest_date = ask(
        f"📅 <b>Earliest Acceptable Date:</b>\nDefault: {defaults['earliest_date']}",
        default=defaults["earliest_date"],
        validator=is_valid_date,
        error_msg="❌ Invalid date. Use YYYY-MM-DD."
    )

    latest_date = ask(
        f"📅 <b>Latest Acceptable Date:</b>\nDefault: {defaults['latest_date']}",
        default=defaults["latest_date"],
        validator=is_valid_date,
        error_msg="❌ Invalid date. Use YYYY-MM-DD."
    )

    current_date = ask(
        f"📅 <b>Current Booking Date:</b>\nDefault: {defaults['current_date']}",
        default=defaults["current_date"],
        validator=is_valid_date,
        error_msg="❌ Invalid date. Use YYYY-MM-DD."
    )

    check_interval = ask(
        f"⏱️ <b>Check Interval (seconds):</b>\nDefault: {defaults['check_interval']}",
        default=str(defaults["check_interval"]),
        validator=is_valid_interval,
        error_msg="❌ Invalid number. Enter a positive integer."
    )

    return {
        "email": email,
        "password": password,
        "location": location,
        "location2": location2,
        "earliest_date": earliest_date,
        "latest_date": latest_date,
        "current_date": current_date,
        "check_interval": int(check_interval),
    }
