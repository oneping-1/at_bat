import time
from typing import List
import json
import requests
from src.scoreboard_data import ScoreboardData
from src.statsapi_plus import get_daily_gamepks

def get_ip() -> str:
    # return 'http://127.0.0.1:5000'
    return "http://192.168.1.133:5000"

def send_data(game_index: int, data: dict):
    ip = get_ip()
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{ip}/{game_index}', headers=headers, data=json.dumps(data), timeout=10)
    print(json.dumps(response.json()))

def start_games(delay_seconds: int = 60) -> List[ScoreboardData]:
    gamepks = get_daily_gamepks()
    games = [ScoreboardData(gamepk=gamepk, delay_seconds=delay_seconds) for gamepk in gamepks]

    for i, game in enumerate(games):
        if game is not None:
            data = game.to_dict()
            send_data(i, data)

    return games

def loop(index: int, game: ScoreboardData):
    if game is None:
        return

    diff = game.get_updated_data_dict()

    if diff:
        send_data(index, diff)

def main():
    games = start_games(delay_seconds=0)
    gamepks = get_daily_gamepks()
    last_gamepk_check = time.time()

    while True:
        for i, game in enumerate(games):
            loop(i, game)

        # if (time.time() - last_gamepk_check) > 600:
        #     last_gamepk_check = time.time()

        #     if gamepks != get_daily_gamepks():
        #         gamepks = get_daily_gamepks()
        #         games = start_games(delay_seconds=0)



if __name__ == '__main__':
    main()
