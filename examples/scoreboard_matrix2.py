"""
This module will send data to the server for the scoreboard matrix.
"""

import time
from typing import Union
import json
import threading
import requests
from flask import Flask, request, jsonify
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
    return 'http://127.0.0.1:5000'
    # return 'http://192.168.1.93:5000'

def send_data(endpoint: str, data: dict):
    """
    Sends dictionary data to the server.

    Args:
        game_index (int): game index to send data to
        data (dict): data to send to the server
    """
    ip = get_ip()

    headers = {'Content-Type': 'application/json'}
    url = f'{ip}/{endpoint}'
    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
    print(json.dumps(response.json(), indent=4))

class Server:
    """
    Server class to send data to the server.
    """
    def __init__(self, scorebaord: 'Scoreboard', gamecast: 'Gamecast'):
        self.scoreboard = scorebaord
        self.gamecast = gamecast
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'home', self.home, methods=['GET'])

    def home(self):
        """
        Make sure the server is running.
        """
        delay = request.args.get('delay')
        gamecast_id = request.args.get('gamecast_id')

        if delay is not None:
            self.scoreboard.delay_seconds = int(delay)

        if gamecast_id is not None:
            self.gamecast.gamecast_id = int(gamecast_id)

        details = {
            'delay_seconds': self.scoreboard.delay_seconds,
            'gamecast_id': self.gamecast.gamecast_id,
            'max_gamecast_id': len(self.scoreboard.games) - 1
        }

        game_details = []
        for game in self.scoreboard.games:
            game_details.append(game.to_dict())

        return_dict = {
            'details': details,
            'games': game_details
        }

        return jsonify(return_dict), 200

    def run(self):
        """
        Run the server.
        """
        self.app.run(host='0.0.0.0', port=5001)

class Gamecast:
    def __init__(self, scoreboard: 'Scoreboard'):
        self.scoreboard = scoreboard

        # gamepk of the game for the gamecast
        self.gamepk: int = None

        # Id of the game on that day shown on scoreboard
        self._gamecast_id = None

        self.game: 'ScoreboardData' = None

        # steals the delay_seconds from the scoreboard
        self.delay_seconds = self.scoreboard.delay_seconds

    @property
    def gamecast_id(self):
        return self._gamecast_id

    @gamecast_id.setter
    def gamecast_id(self, value):
        max_value = len(self.scoreboard.games) - 1

        if value > max_value:
            self._gamecast_id = None
            return

        self._gamecast_id = value
        self.gamepk = self.scoreboard.games[value].gamepk
        self.game = ScoreboardData(gamepk=self.gamepk, delay_seconds=self.delay_seconds)
        send_data('gamecast', self.game.to_dict())

    def _loop(self):
        if self.game is None:
            return

        # Update in case recent changed
        self.delay_seconds = self.scoreboard.delay_seconds

        diff = self.game.get_updated_data_dict(delay_seconds=self.delay_seconds)

        if diff:
            send_data('gamecast', diff)

    def run(self):
        """
        Main function to run the gamecast
        """
        while True:
            self._loop()

class Scoreboard:
    """
    ScoreboardMatrix class to send data to the server for the scoreboard matrix.
    """
    def __init__(self, delay_seconds: int = 60):
        self.delay_seconds = delay_seconds
        self.games = []
        self.gamepks = []
        self.last_gamepk_check = time.time()

    def reset_games(self):
        """
        Resets the games on the server.
        """
        ip = get_ip()
        url = f'{ip}/reset'
        response = requests.get(url, timeout=10)
        print(json.dumps(response.json(), indent=4))

    def start_games(self):
        """
        Starts the games and sends the initial data to the server.

        Returns:
            List[ScoreboardData]: List of ScoreboardData objects
        """
        self.reset_games()
        self.gamepks = get_daily_gamepks()

        self.games = []
        for gamepk in self.gamepks:
            self.games.append(ScoreboardData(gamepk=gamepk, delay_seconds=self.delay_seconds))

        for i, game in enumerate(self.games):
            if game is not None:
                data = game.to_dict()
                send_data(i, data)

    def check_for_new_games(self):
        """
        Check for new games and send the new data to the server.

        Returns:
            List[int]: List of gamepks
        """
        new_gamepks = get_daily_gamepks()

        if self.gamepks != new_gamepks:
            self.gamepks = new_gamepks
            self.start_games()

    def loop(self, index: int, game: Union[ScoreboardData, None]):
        """
        Main loop to check for updated data and send it to the server.

        Args:
            index (int): index of the game
            game (ScoreboardData): ScoreboardData object
        """
        if game is None:
            return

        diff = game.get_updated_data_dict(delay_seconds=self.delay_seconds)

        if diff:
            send_data(index, diff)

    def run(self):
        """
        Main function to start the games and run the main loop.
        The main loop will check for updated data and send it to the server.

        This function also checks if the daily gamepks change and will
        send the new data to the server.
        """
        self.start_games()

        while True:
            for i, game in enumerate(self.games):
                try:
                    self.loop(i, game)
                except TimeoutError as e:
                    print('Timeout Error')
                    print(e)

            if (time.time() - self.last_gamepk_check) > 600:
                self.last_gamepk_check = time.time()
                self.check_for_new_games()

def main():
    scoreboard = Scoreboard()
    gamecast = Gamecast(scoreboard)
    server = Server(scorebaord=scoreboard, gamecast=gamecast)

    server_thread = threading.Thread(target=server.run)
    scoreboard_thread = threading.Thread(target=scoreboard.run)
    gamecast_thread = threading.Thread(target=gamecast.run)

    server_thread.start()
    scoreboard_thread.start()
    gamecast_thread.start()

if __name__ == '__main__':
    main()
