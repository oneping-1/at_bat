"""
This module is used to send data to the server for the scoreboard matrix.
If this module is being run on a Raspberry Pi, you will need to use
Gunicorn to run the server instead of python/Flask. Gunicorn can easily
be installed using pip install gunicorn.

In the terminal, navigate to the directory where this file is located
and run the following command:
gunicorn -w 1 -b 0.0.0.0:8080 scoreboard_matrix2:app

to run on lower port like 80 (linux only):
sudo apt install nginx
sudo nano /etc/nginx/sites-available/scoreboard_matrix2.py

server {
    listen 80;
    server_name your_domain_or_IP; # add http://

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_redirect off;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

sudo ln -s /etc/nginx/sites-available/scoreboard_matrix2 /etc/nginx/sites-enabled/
sudo nginx -t # test config
sudo systemctl restart nginx

# if all that doesnt work try:
sudo rm /etc/nginx/sites-enabled/default

lastly in crontab -e add:
@reboot sleep 10; source /home/ondeck/venv/bin/activate; cd /home/ondeck/MLB/examples; /home/ondeck/venv/bin/gunicorn -w 1 --bind 0.0.0.0:8080 scoreboard_matrix2:app >> /home/ondeck/scoreboard_matrix2.log 2>&1 &
"""

import platform
import time
from typing import Union, List
import sys
import json
import threading
import os
import requests
from flask import Flask, request, Response, Blueprint
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
    l = sap.get_daily_gamepks()
    return l

class Server:
    """
    Server class to send data to the server.
    """
    def __init__(self, scoreboard: 'Scoreboard', gamecast: 'Gamecast'):
        self.scoreboard = scoreboard
        self.gamecast = gamecast
        self.restart_given = False

        self.blueprint = Blueprint('server', __name__)

        self.blueprint.add_url_rule('/', 'home', self.home, methods=['GET'])
        self.blueprint.add_url_rule('/<int:gamepk>', 'gamepk', self.gamepk, methods=['GET'])
        self.blueprint.add_url_rule('/restart', 'restart', self.restart, methods=['GET'])
        self.blueprint.add_url_rule('/settings', 'settings', self.settings, methods=['GET'])

    def home(self):
        """
        Make sure the server is running.
        """
        game_details = [game.to_dict() for game in self.scoreboard.games]
        return_dict = {'games': game_details}
        r = json.dumps(return_dict, indent=4)
        print(r)
        return Response(r, mimetype='text/plain')

    def gamepk(self, gamepk: int):
        """
        Get the game data for the given gamepk.
        """
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
        sys.stdout.flush()
        os.system('sudo reboot')
        return Response('Server not restarted', mimetype='text/plain')

    def settings(self):
        """
        Set the settings for the server.
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

        return Response(json.dumps(details, indent=4), mimetype='text/plain')

class Gamecast:
    """
    Gamecast class to send data to the server for the gamecast. This
    class will only send data for the game that is being shown on the
    scoreboard.
    """
    def __init__(self, scoreboard: 'Scoreboard'):
        self.scoreboard = scoreboard
        self.gamepk: int = None
        self._gamecast_id: int = None
        self.game: 'ScoreboardData' = None
        self.delay_seconds = self.scoreboard.delay_seconds

    @property
    def gamecast_id(self) -> int:
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
            time.sleep(.1)

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
        """
        new_gamepks = get_daily_gamepks()

        if self.gamepks != new_gamepks:
            self.gamepks = new_gamepks
            self.start_games()

    def update_and_send_game(self, index: int, game: Union[ScoreboardData, None]):
        """
        Main loop to check for updated data and send it to the server.
        """
        if game is None:
            return

        diff = game.update_return_difference(delay_seconds=self.delay_seconds)

        if diff:
            send_data(index, diff)

    def run(self):
        """
        Main function to start the games and run the main loop.
        """
        self.start_games()

        while True:
            for i, game in enumerate(self.games):
                self.update_and_send_game(i, game)
                time.sleep(5)

            if (time.time() - self.last_gamepk_check) > 60:
                self.last_gamepk_check = time.time()
                self.check_for_new_games()

def create_app():
    """
    App factory function to create and configure the Flask app.
    """
    app = Flask(__name__)

    scoreboard = Scoreboard()
    gamecast = Gamecast(scoreboard)
    server = Server(scoreboard=scoreboard, gamecast=gamecast)

    app.register_blueprint(server.blueprint)

    # Start threads for scoreboard and gamecast
    scoreboard_thread = threading.Thread(target=scoreboard.run, daemon=True)
    gamecast_thread = threading.Thread(target=gamecast.run, daemon=True)

    scoreboard_thread.start()
    gamecast_thread.start()

    return app

# Create the app at the module level so Gunicorn can find it
app = create_app()

def main():
    """
    Main function to run the server when executing the script directly.
    """
    if platform.system() == 'Windows':
        app.run(host='0.0.0.0', port=80)
    else:
        # On Raspberry Pi or other systems, use Gunicorn to run the app
        pass

if __name__ == '__main__':
    main()
