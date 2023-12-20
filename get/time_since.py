"""
Used for testing purposes
Mainly during the offseason
Chatgpt wrote this all for me
"""

from datetime import datetime
import pytz

def seconds_since(time_str, timezone_str):
    """
    Calculate the number of seconds since a given time in a specified timezone.

    Parameters:
    time_str (str): The time in ISO 8601 format.
    timezone_str (str): The timezone as a string, e.g., 'America/New_York'.

    Returns:
    int: The number of seconds since the given time.
    """
    # Parse the time string
    input_time = datetime.fromisoformat(time_str)

    # Convert the input time to the specified timezone
    tz = pytz.timezone(timezone_str)
    localized_time = tz.localize(input_time)

    # Get the current time in the same timezone
    now = datetime.now(tz)

    # Calculate the difference in seconds
    difference = (now - localized_time).total_seconds()

    return int(difference)

# Example usage
TIME_STR = "2023-05-29T12:30:00"
TIMEZONE_STR = "America/Chicago"
print(seconds_since(TIME_STR, TIMEZONE_STR))
