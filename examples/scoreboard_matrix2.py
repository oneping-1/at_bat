"""
This module will send data to the server for the scoreboard matrix.
"""

import time
from typing import Union
import json
import requests
from flask import Flask, request, jsonify
from src.scoreboard_data import ScoreboardData
from src.statsapi_plus import get_daily_gamepks

class Server:
    """
    Server class to send data to the server.
    """
    def __init__(self, scorebaord_matrix: 'ScoreboardMatrix'):
        self.scoreboard_matrix = scorebaord_matrix
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'home', self.home, methods=['GET'])
        self.app.run(host='0.0.0.0', port=5000)

    def home(self):
        """
        Make sure the server is running.
        """
        delay = request.args.get('delay')

        if delay is not None:
            self.scoreboard_matrix.delay_seconds = int(delay)

        return jsonify({'delay_seconds': self.scoreboard_matrix.delay_seconds})

class ScoreboardMatrix:
    """
    ScoreboardMatrix class to send data to the server for the scoreboard matrix.
    """
    def __init__(self, delay_seconds: int = 60):
        self.delay_seconds = delay_seconds
        self.games = []
        self.gamepks = []
        self.last_gamepk_check = time.time()
        self.ip = self.get_ip()

    def get_ip(self) -> str:
        """
        Returns the IP address of the server to send data to. A function
        is used in case future me wants to store this data in a file or
        database.

        Returns:
            str: The IP address of the server to send data to.
        """
        # return '127.0.0.1:5000'
        return 'http://192.168.1.93:5000'

    def send_data(self, game_index: int, data: dict):
        """
        Sends dictionary data to the server.

        Args:
            game_index (int): game index to send data to
            data (dict): data to send to the server
        """
        headers = {'Content-Type': 'application/json'}
        url = f'{self.ip}/{game_index}'
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        print(json.dumps(response.json(), indent=4))

    def reset_games(self):
        """
        Resets the games on the server.
        """
        url = f'{self.ip}/reset'
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
        self.games = [ScoreboardData(gamepk=gamepk, delay_seconds=self.delay_seconds) for gamepk in self.gamepks]

        for i, game in enumerate(self.games):
            if game is not None:
                data = game.to_dict()
                self.send_data(i, data)

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
            self.send_data(index, diff)

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

if __name__ == '__main__':
    scoreboard_matrix = ScoreboardMatrix(delay_seconds=60)
    server = Server(scorebaord_matrix=scoreboard_matrix)
    scoreboard_matrix.run()
