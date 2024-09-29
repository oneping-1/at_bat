"""
This module will send data to the server for the scoreboard matrix.
"""

import time
from typing import Union, List
import sys
import json
import threading
import os
import requests
from flask import Flask, request, Response
from src.scoreboard_data import ScoreboardData
from src import statsapi_plus as sap

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
    requests.post(url, headers=headers, data=json.dumps(data), timeout=10)

    # Only show new data to limit the amount of data shown
    # but add endpoint so we know what data is being shown
    # if there is an error here its probably on the scoreboard side
    # new_data = response.json()['new_data']
    # new_data['endpoint'] = endpoint

    # print(json.dumps(new_data, indent=4))

def get_daily_gamepks() -> List[int]:
    """
    Get the daily gamepks.
    One function in case future me wants to add more functionality.
    Or add specific gamepks.

    Returns:
        list: List of gamepks
    """
    l =  sap.get_daily_gamepks()

    return l

class Server:
    """
    Server class to send data to the server.
    """
    def __init__(self, scorebaord: 'Scoreboard', gamecast: 'Gamecast'):
        self.scoreboard = scorebaord
        self.gamecast = gamecast
        self.restart_given = False
        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'home', self.home, methods=['GET'])
        self.app.add_url_rule('/<int:gamepk>', 'gamepk', self.gamepk, methods=['GET'])
        self.app.add_url_rule('/restart', 'restart', self.restart, methods=['GET'])

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
            'max_gamecast_id': len(self.scoreboard.games) - 1,
            'restart_given': self.restart_given
        }

        game_details = []
        for game in self.scoreboard.games:
            game_details.append(game.to_dict())

        return_dict = {
            'details': details,
            'games': game_details
        }

        r = json.dumps(return_dict, indent=4)
        print(r)

        return Response(r, mimetype='text/plain')

    def gamepk(self, gamepk: int):
        """
        Get the game data for the given gamepk.

        Args:
            gamepk (int): gamepk of the game
        """
        gamepk = request.view_args['gamepk']
        game = ScoreboardData(gamepk=gamepk, delay_seconds=self.scoreboard.delay_seconds)
        game = game.to_dict()
        return Response(json.dumps(game, indent=4), mimetype='text/plain')

    def restart(self):
        """
        Restart the server by rebooting the Raspberry Pi.
        Could not find a way to restart the server without rebooting.
        """

        self.restart_given = True
        print('sudo reboot')
        # time.sleep(5)

        sys.stdout.flush()
        os.system('sudo reboot')

        # shouldnt return anything since the server is restarting
        # but here just in case
        return Response('Server not restarted', mimetype='text/plain')

    def run(self):
        """
        Run the server.
        """
        self.app.run(host='0.0.0.0', port=80)

class Gamecast:
    """
    Gamecast class to send data to the server for the gamecast. This
    class will only send data for the game that is being shown on the
    scoreboard.
    """
    def __init__(self, scoreboard: 'Scoreboard'):
        self.scoreboard = scoreboard

        # gamepk of the game for the gamecast
        self.gamepk: int = None

        # Id of the game on that day shown on scoreboard
        self._gamecast_id: int = None

        self.game: 'ScoreboardData' = None

        # steals the delay_seconds from the scoreboard
        self.delay_seconds = self.scoreboard.delay_seconds

    @property
    def gamecast_id(self) -> int:
        """
        Getter for gamecast_id property. This will return the gamecast_id
        property. If the gamecast_id is greater than the max value, it will
        return None.

        Returns:
            int: gamecast_id
        """
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

        diff = self.game.update_return_difference(delay_seconds=self.delay_seconds)

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
        for i, gamepk in enumerate(self.gamepks):
            game = ScoreboardData(gamepk=gamepk, delay_seconds=self.delay_seconds)
            data = game.to_dict()
            send_data(i, data)

            self.games.append(game)

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

        diff = game.update_return_difference(delay_seconds=self.delay_seconds)\

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

            if (time.time() - self.last_gamepk_check) > 60:
                self.last_gamepk_check = time.time()
                self.check_for_new_games()

def main():
    """
    Main function to run the server, scoreboard, and gamecast.
    """
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
