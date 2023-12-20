"""
Sends data to an ESP32 so that it can be displayed on a
scoreboard matrix.
"""

import os
from typing import List
import requests
from get.statsapi_plus import get_daily_gamepks
from get.game import Game
from get.scoreboard_data import ScoreboardData

PORT = 8080 # Defined on ESP32's side. Cant really change it.
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
    """
    Gets the current ip address of the ESP32 from ip.txt
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(csv_dir, 'ip.txt')

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        ip = file.read()

    return ip

def start_games_simple(ip: str, delay_seconds: int = 0) -> List[ScoreboardData]:
    """Initalizes the games list with the games from the current day.
    Sends initial data to the ESP32.

    Returns:
        List[ScoreboardData]: list of games from the current day
    """
    daily_pks = get_daily_gamepks('2023-05-29')
    games: List[ScoreboardData] = []

    for i, pk in enumerate(daily_pks):
        game = Game.get_game_from_pk(pk)
        game_simple = ScoreboardData(game, delay_seconds=delay_seconds)
        games.append(game_simple)

        response = requests.get(f'http://{ip}:{PORT}/{i}', timeout=10,
                                params=get_request_dict(game_simple))

        if response.status_code != 200:
            print(f'Error: {response.status_code} {response.reason}')

        print(response.url)

    return games

def get_request_dict(game: ScoreboardData) -> dict:
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
    diff = game.update()

    if diff:
        response = requests.get(f'http://{ip}/{i}', timeout=10,
                                params=diff.to_dict())

        if response.status_code != 200:
            print(f'Error: {response.status_code} {response.reason}')

        print(response.url)

def main():
    """Main function that runs the scoreboard matrix"""
    ip = get_ip()
    start_games_simple(ip, delay_seconds=0)

    # games = start_games_simple(ip)
    # while True:
    #     for i, game, in enumerate(games):
    #         loop(ip, i, game)

if '__main__' == __name__:
    main()
