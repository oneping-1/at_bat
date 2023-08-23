"""
Basically a utils module for other modules throughout the project.
Eventually want to get rid of this module by moving these functions to
more appropriate modules
"""

from typing import List
import csv
from datetime import datetime, timedelta
import os
import statsapi
from colorama import Fore
import numpy as np


def get_game_dict(gamePk=None, delay_seconds=0) -> dict:
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
    if gamePk is None:
        raise ValueError('gamePk not provided')

    delay_time = _get_utc_time(delay_seconds=delay_seconds)
    data = statsapi.get('game',
                        {'gamePk': gamePk, 'timecode': delay_time},
                        force=True)
    return data


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


def get_daily_gamePks(date: str = None) -> List[int]:
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


def get_color(team_abv:str, division:str) -> Fore:
    """
    Takes a team and their division and outputs a color. Used for me
    because these are the teams that are important to me

    Args:
        team_abv (str): The team abbreviations
        division (str): The division of the team

    Returns:
        Fore: A colorama Fore class for the given color
    """
    if team_abv == 'TEX':
        return Fore.LIGHTBLUE_EX
    if division == 'AW':
        return Fore.LIGHTRED_EX
    return Fore.WHITE


def get_run_expectency_numpy() -> np.ndarray:
    """
    Returns the numpy array run expectency table

    Run expectency table obtained from:
    https://community.fangraphs.com/the-effect-of-umpires-on-baseball-umpire-runs-created-urc/

    How to index:
    renp[balls][strikes][outs][runners]
    where runners is a int obtained from get_runners_int() function

    Args:
        None

    Raises:
        FileNotFoundError: re_fangraph.csv file missing, renamed, or misplaced

    Returns:
        numpy.ndarray: Run expectency table renp[balls][strikes][outs][runners]
    """
    current_dir = os.path.dirname(os.path.relpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(csv_path, 're_fangraph.csv')

    renp = np.zeros((5,4,4,8))

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            balls = int(row[0])
            strikes = int(row[1])
            outs = int(row[2])
            runners = int(row[3])
            run_expectency = float(row[4])

            renp[balls][strikes][outs][runners] = run_expectency

    return renp


def get_run_expectency_difference_numpy() -> np.ndarray:
    """
    Returns the numpy array run expectency table

    Run expectency table obtained from:
    https://community.fangraphs.com/the-effect-of-umpires-on-baseball-umpire-runs-created-urc/

    How to index:
    renp[balls][strikes][outs][runners]
    where runners is a int obtained from int(Runners)

    Raises:
        FileNotFoundError: red_fangraph.csv file missing, renamed, or misplaced

    Returns:
        np.ndarray: Run expectency table
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(csv_path, 'red_fangraph.csv')
    rednp = np.zeros((5,4,4,8))

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            balls = int(row[0])
            strikes = int(row[1])
            outs = int(row[2])
            runners = int(row[3])
            run_expectency = float(row[4])

            rednp[balls][strikes][outs][runners] = run_expectency

    return rednp


if __name__ == '__main__':
    statsapi.schedule()
