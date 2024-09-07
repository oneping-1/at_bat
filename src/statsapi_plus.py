"""
Basically a utils module for other modules throughout the project.
Eventually want to get rid of this module by moving these functions to
more appropriate modules
"""

from typing import List, Union
from datetime import datetime, timedelta
from dateutil import tz
import os
import statsapi
import pandas as pd

def get_game_dict(gamepk: int = None, time: Union[str, None] = None,
    delay_seconds: Union[int, None] = 0) -> dict:
    """
    Returns the game data for a given gamePk. If time is provided, the game
    data at that time is returned. If time is not provided, the game data
    at the current time is returned.

    Args:
        gamepk (int): gamepk for the desired game. Defaults to None.
        time (str, optional): time (ISO 8601). Defaults to None.
        delay_seconds (int, optional): number of seconds to be delayed.
            Defaults to 0.

    Raises:
        ValueError: No gamepk  provided
        MaxRetriesError: Max retries reached

    Returns:
        dict: The game data for the given gamePk
    """
    max_retries = 10

    if gamepk is None:
        raise ValueError('gamePk not provided')

    if time is not None:
        delay_time = _get_utc_time_from_zulu(time)
    else:
        delay_time = _get_utc_time(delay_seconds=delay_seconds)

    for i in range(max_retries):
        try:
            data = statsapi.get('game',
                {'gamePk': gamepk, 'timecode': delay_time},
                force=True)
            return data
        except ConnectionError as e:
            print(f'ConnectionError: {e}')
            print(f'Retrying... {i+1}/{max_retries}')
            time.sleep(2 ** i) # Exponential backoff
    raise MaxRetriesError('Max retries reached')

def _get_utc_time(delay_seconds: int = 0):
    """
    returns the utc time in YYYMMDD-HHMMSS in 24 hour time

    Used for statsapi.get() functions that use time parameter
    'delay_seconds' can also be type float as well

    Args:
        delay_seconds (int, optional): Seconds behind present you want
        the output to be. Defaults to 0

    Raises:
        TypeError: If 'delay_seconds' is type str

    Returns:
        str: The UTC time in the 'YYYYMMDD-HHMMSS' format
    """
    # Get the current time in UTC
    utc_time = datetime.utcnow()

    # Subtract the delta
    utc_time = utc_time - timedelta(seconds=delay_seconds)

    # Format the time
    formatted_time = utc_time.strftime('%Y%m%d_%H%M%S')

    return formatted_time

def _get_utc_time_from_zulu(zulu_time_str):
    # Parse the time string with a timezone offset
    utc_time = datetime.fromisoformat(zulu_time_str.replace('Z', '+00:00'))

    # Convert to UTC (Zulu time)
    utc_time = utc_time.astimezone(tz.UTC)

    # Return the formatted UTC time in the desired format
    return utc_time.strftime('%Y%m%d_%H%M%S')

def get_daily_gamepks(date: str = None) -> List[int]:
    """
    Returns a list of gamePks for a given day in ISO 8601 format
    (YYYY-MM-DD).

    Args:
        date (str, optional): The current date in ISO 8601 format,
            YYYY-MM-DD. Defaults to present date.

    Returns:
        List[int]: List of gamePks for given dates. Should
            be sorted by start time.

    Raises:
        TypeError: If date argument is not type str

    Example:
        gamePk_list = get_daily_gamePks(date='2023-07-18')
        for gamePk in gamePk_list:
            # code
    """
    gamePks = []

    if date is not None:
        data = statsapi.schedule(date=date)
    elif date is None:
        data = statsapi.schedule()

    for game in data:
        gamePks.append(game['game_id'])

    return gamePks

def get_re288_dataframe() -> pd.DataFrame:
    """
    Returns the re288.csv file as a pandas DataFrame

    Returns:
        pd.DataFrame: The re288.csv file as a pandas DataFrame
    """
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 're288.csv')

    return pd.read_csv(csv_file_path)

def get_re640_dataframe() -> pd.DataFrame:
    """
    Returns the re640.csv file as a pandas DataFrame

    Returns:
        pd.DataFrame: The re640.csv file as a pandas DataFrame
    """
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 're640.csv')

    return pd.read_csv(csv_file_path)

def get_wp780800_dataframe() -> pd.DataFrame:
    """
    Returns the wp780800.csv file as a pandas DataFrame

    Returns:
        pd.DataFrame: The wp780800.csv file as a pandas DataFrame
    """
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 'wp780800.csv')

    return pd.read_csv(csv_file_path)

def get_wpd351360_dataframe() -> pd.DataFrame:
    """
    Returns the wpd351360.csv file as a pandas DataFrame

    Returns:
        pd.DataFrame: The wpd351360.csv file as a pandas DataFrame
    """
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 'wpd351360.csv')

    return pd.read_csv(csv_file_path)


def _read_runners(base: str) -> bool:
    if base == 'True':
        return True
    if base == 'False':
        return False
    raise ValueError('unknown')


def get_red288_dataframe() -> pd.DataFrame:
    """
    Returns the red288.csv file as a pandas DataFrame

    Returns:
        pd.DataFrame: The red288.csv file as a pandas DataFrame
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 'red288.csv')

    return pd.read_csv(csv_file_path)

if __name__ == '__main__':
    print(get_game_dict(745995))
