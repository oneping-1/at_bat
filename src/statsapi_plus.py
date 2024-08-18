"""
Basically a utils module for other modules throughout the project.
Eventually want to get rid of this module by moving these functions to
more appropriate modules
"""

from typing import List
import time
from datetime import datetime, timedelta
import os
import statsapi
import pandas as pd

class MaxRetriesError(Exception):
    pass

def get_game_dict(gamepk=None, delay_seconds=0) -> dict:
    """
    Returns the game dictionary for given game

    Essentially the same as statsapi.get('game') but with an extra
    function argument. This argument will let the dictionary returned
    to be from a given number of seconds ago. This is for when you are
    watching a game which is delayed to the data

    Args:
        gamePk (int): The gamePk/id for the desired game. Can easily
            be found on the MLB/MiLB websites
        delay_seconds (float, optional): The number of seconds the data
            should be delayed to match what you're seeing. Defaults to 0

    Raises:
        ValueError: If gamePk argument is not defined
        ConnectionError: If connection to API fails
        TypeError: If delay_seconds is not valid

    Returns:
        dict: The game dictionary recieved with the given delay. Can be
            turned into a Game object by using this dict as the only
            argument to Game. Example:
            data = get_game_dict(717404, delay_seconds=45)
            game_class = Game(data)

    Example:
        game_dict = get_game_dict(gamePk=718552, delay_seconds=30)
        game_class = Game(game_dict)
    """
    max_retries = 10

    if gamepk is None:
        raise ValueError('gamePk not provided')

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
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 're288.csv')

    return pd.read_csv(csv_file_path)

def get_re640_dataframe() -> pd.DataFrame:
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 're640.csv')

    return pd.read_csv(csv_file_path)

def get_wp702720_dataframe() -> pd.DataFrame:
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 'wp702720.csv')

    return pd.read_csv(csv_file_path)


def _read_runners(base: str) -> bool:
    if base == 'True':
        return True
    elif base == 'False':
        return False
    raise ValueError('unknown')


def get_red288_dataframe() -> pd.DataFrame:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, '..', 'every_pitch_csv')
    csv_file_path = os.path.join(csv_path, 'red288.csv')

    return pd.read_csv(csv_file_path)

if __name__ == '__main__':
    print(get_game_dict(745995))
