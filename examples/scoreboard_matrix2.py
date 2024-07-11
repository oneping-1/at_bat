"""
This module will send data to the server for the scoreboard matrix.
"""

import time
from typing import List
import json
import requests
from src.scoreboard_data import ScoreboardData
from src.statsapi_plus import get_daily_gamepks

def get_ip() -> str:
    """
    Returns the IP address of the server to send data to. A function
    is used in case future me wants to store this data in a file or
    database.

    Returns:
        str: The IP address of the server to send data to.
    """
    # return 'http://127.0.0.1:5000'
    return 'http://192.168.1.93:5000'

def send_data(game_index: int, data: dict):
    """
    Sends dictionary data to the server.

    Args:
        game_index (int): game index to send data to
        data (dict): data to send to the server
    """
    ip = get_ip()
    headers = {'Content-Type': 'application/json'}

    url = f'{ip}/{game_index}'
    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
    print(json.dumps(response.json(), indent=4))

def reset_games():
    """
    Resets the games on the server.
    """
    ip = get_ip()
    url = f'{ip}/reset'
    response = requests.get(url, timeout=10)
    print(json.dumps(response.json(), indent=4))

def start_games(delay_seconds: int = 60) -> List[ScoreboardData]:
    """
    Starts the games and sends the initial data to the server.

    Args:
        delay_seconds (int, optional): Seconds to delay the data. Useful
            when watching games live as streams are typically delayed.
            60 seconds is a good number when watching MLB.tv
            Defaults to 60.

    Returns:
        List[ScoreboardData]: List of ScoreboardData objects
    """
    # reset_games()
    gamepks = get_daily_gamepks()
    games = [ScoreboardData(gamepk=gamepk, delay_seconds=delay_seconds) for gamepk in gamepks]

    for i, game in enumerate(games):
        if game is not None:
            data = game.to_dict()
            send_data(i, data)

    return games

def check_for_new_games(gamepks: List[int]) -> List[int]:
    new_gamepks = get_daily_gamepks()

    if gamepks != new_gamepks:
        return new_gamepks

    return gamepks

def loop(index: int, game: ScoreboardData):
    """
    Main loop to check for updated data and send it to the server.

    Args:
        index (int): index of the game
        game (ScoreboardData): ScoreboardData object
    """
    if game is None:
        return

    diff = game.get_updated_data_dict()

    if diff:
        send_data(index, diff)

def main(delay_seconds: int = 60):
    """
    Main function to start the games and run the main loop.
    The main loop will check for updated data and send it to the server.

    This function also checks if the daily gamepks change and will
    send the new data to the server.
    """
    games = start_games(delay_seconds=delay_seconds)
    gamepks = get_daily_gamepks()
    last_gamepk_check = time.time()

    while True:
        for i, game in enumerate(games):
            try:
                loop(i, game)
            except TimeoutError as e:
                print('Timeout Error')
                print(e)

        if (time.time() - last_gamepk_check) > 600:
            last_gamepk_check = time.time()
            gamepks = check_for_new_games(gamepks)

if __name__ == '__main__':
    main()
