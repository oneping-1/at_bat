"""
Sends data to an ESP32 so that it can be displayed on a
scoreboard matrix.
"""

import time
import sys
from typing import List
from datetime import datetime, timezone, timedelta
import requests
from src.statsapi_plus import get_daily_gamepks
from src.game import Game
from src.scoreboard_data import ScoreboardData

PORT = 8080 # Defined on the ESP32's side
request_keys = ['game_state',
                'away_abv',
                'home_abv',
                'away_score',
                'home_score',
                'start_time',
                'inning',
                'inning_state',
                'outs',
                'runners',
                'gamepk']

def get_ip() -> str:
    return '192.168.1.187'

def time_since_utc(input_time):
    """
    Returns the date from the input time in ISO 8601 format (converted
    to UTC) and the time in seconds since the input time. The input time
    is expected to be in ISO 8601 format.

    Used to test when there are no games on the current day like during
    the offseason. The input time is the time of the last game of the
    previous day.

    Args:
        input_time (str): ISO 8601 formatted time

    Returns:
        Tuple[str, int]: Tuple containing the date in ISO 8601 format
            and the time difference in seconds
    """
    # Parsing the input time
    input_datetime = datetime.fromisoformat(input_time)

    # Converting the input time to UTC
    input_datetime_utc = input_datetime.astimezone(timezone.utc)

    # Extracting the date from the input time in UTC
    input_date_utc = input_datetime_utc.date().isoformat()

    # Getting the current time in UTC
    current_datetime_utc = datetime.now(timezone.utc)

    # Calculating the time difference in seconds
    time_diff_seconds = (current_datetime_utc - input_datetime_utc).total_seconds()

    return input_date_utc, int(time_diff_seconds)

def time_from_seconds_ago_with_offset(seconds_ago, offset_hours):
    """
    Returns the ISO 8601 formatted date and time (without microseconds)
    for a moment 'seconds_ago' seconds in the past from now, adjusted
    for a specific timezone offset, and outputs the time with the
    specified timezone offset.
    """
    # Create a timezone object with the specified offset
    offset_timedelta = timedelta(hours=offset_hours)
    tz = timezone(offset_timedelta)

    # Getting the current time in UTC
    current_datetime_utc = datetime.now(timezone.utc)

    # Calculating the adjusted current time based on the timezone offset
    adjusted_current_datetime = current_datetime_utc + offset_timedelta

    # Calculating the past time by subtracting seconds
    past_datetime = adjusted_current_datetime - timedelta(seconds=seconds_ago)

    # Assign the custom timezone to the datetime object
    past_datetime_with_tz = past_datetime.replace(tzinfo=tz)

    # Removing microseconds from the datetime
    past_datetime_no_micro = past_datetime_with_tz.replace(microsecond=0)

    return past_datetime_no_micro.isoformat()

def start_games(ip: str, date: str, delay_seconds: int) -> List[ScoreboardData]:
    """Initalizes the games list with the games from the current day.
    Sends initial data to the ESP32.

    Returns:
        List[ScoreboardData]: list of games from the current day
    """

    daily_pks = get_daily_gamepks(date)
    games: List[ScoreboardData] = [None] * 16

    for i, pk in enumerate(daily_pks):
        game = Game.get_game_from_pk(pk)
        games[i] = ScoreboardData(game, delay_seconds=delay_seconds)

    for i, game in enumerate(games):
        if game is not None:
            params = get_request_dict(game) | {'show': 'true'}
            response = requests.get(f'http://{ip}:{PORT}/{i}', timeout=10,
                                    params=params)
        else:
            response = requests.get(f'http://{ip}:{PORT}/{i}', timeout=10,
                                    params={'show': 'false'})

        if response.status_code != 200:
            print(f'Error: {response.status_code} {response.reason}')

        print(response.url)

    return games

def get_request_dict(game: ScoreboardData) -> dict:
    """
    Returns a dictionary with the keys and values of the game object

    Args:
        game (ScoreboardData): ScoreboardData object

    Returns:
        dict: Dictionary with the keys and values of the game object
    """
    d = {}
    for key in request_keys:
        d[key] = getattr(game, key)

    return d

def loop(ip: str, i: int, game: ScoreboardData):
    """Update the scoreboard matrix with the current game data.

    Args:
        ip (str): IP address of the ESP32
        i (int): Index of the game in the games list
        game (GameSimple): GameSimple object
    """

    if game is None:
        return

    diff, new_info = game.update_and_return_new()

    if new_info is True:
        response = requests.get(f'http://{ip}:{PORT}/{i}', timeout=10,
                                params=diff.to_dict())

        if response.status_code != 200:
            print(f'Error: {response.status_code} {response.reason}')

        print(response.url)

def main():
    """Main function that runs the scoreboard matrix"""
    time.sleep(10) # Let Raspberry Pi connect to the network from boot
    ip = get_ip()
    games = start_games(ip, date=None, delay_seconds=60)

    # Get new games for the day
    current_gamepks = get_daily_gamepks()
    last_gamepk_check = time.time()

    while True:
        for i, game, in enumerate(games):
            try:
                loop(ip, i, game)
            except KeyboardInterrupt:
                sys.exit()

        if (time.time() - last_gamepk_check) > 600:
            last_gamepk_check = time.time()
            new_gamepks = get_daily_gamepks()

            if new_gamepks != current_gamepks:
                games = start_games(ip, date=None, delay_seconds=60)

if '__main__' == __name__:
    main()
