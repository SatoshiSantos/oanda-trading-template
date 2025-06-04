# core/trading_time.py

from datetime import datetime
import pytz


def is_within_trading_window(config: dict) -> bool:
    """
    Check if current time is within the allowed trading window.
    Converts user-selected local times to UTC for comparison.
    """

    try:
        # Parse start and end time in ISO format from GUI (assumed local timezone)
        local_tz = pytz.timezone(
            "America/New_York"
        )  # Update to match user region dynamically if needed
        start_local = local_tz.localize(datetime.fromisoformat(config["start_time"]))
        end_local = local_tz.localize(datetime.fromisoformat(config["end_time"]))

        # Convert both to UTC for comparison with current UTC time
        start_utc = start_local.astimezone(pytz.utc)
        end_utc = end_local.astimezone(pytz.utc)
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

        return start_utc <= now_utc <= end_utc

    except Exception as e:
        print(f"[Trading Time] Error parsing trading window: {e}")
        return False
