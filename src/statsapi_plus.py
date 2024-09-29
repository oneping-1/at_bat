"""
Basically a utils module for other modules throughout the project.
Eventually want to get rid of this module by moving these functions to
more appropriate modules
"""

from typing import List
import os
import statsapi
import pandas as pd

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

def find_division_from_id() -> str:
    """
    Returns the division of a team given the team_id

    Returns:
        str: The division of a team given the team_id
    """
    d = {}

    csv_path = os.path.join(os.path.dirname(os.path.relpath(__file__)), '..', 'csv')
    teams = os.path.join(csv_path, 'teams.csv')

    for team in teams:
        d[team['team_id']] = team['division']

    return d
