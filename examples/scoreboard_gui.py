"""
This module creates a GUI for the MLB scoreboard. The scoreboard displays
the current games being played and the current time and date. The GUI is
created using the tkinter library. The scoreboard is updated every 5 seconds
to display the most recent game data.
"""

import os
from datetime import datetime, timedelta
from typing import List, Tuple
import argparse
import tkinter as tk
import threading
from PIL import Image, ImageTk
from at_bat.statsapi_plus import get_daily_gamepks
from at_bat.scoreboard_data import ScoreboardData

class GameFrame(tk.Frame):
    """.
    GameFrame class is a frame that displays the current game information.
    The game information includes the team abbreviations, scores, inning, and
    runners on base. The frame is color coded based on the game state.`
    """
    _BOARDER_WIDTH = 0
    _BW = _BOARDER_WIDTH

    _FONT_BIG = ('Consolas', 22, 'bold')
    _FONT_SMALL = ('Consolas', 12, 'bold')
    _ARROW_FONT = ('Consolas', 18, 'bold')

    LIVE_COLOR = 'white'
    NOT_LIVE_COLOR = 'light grey'

    RIVAL_TEAMS = ()
    RIVAL_COLOR = 'firebrick1'
    FAV_TEAMS = 'TEX'
    FAV_COLOR = 'blue'
    BET_TEAMS = ()
    BET_COLOR = 'green'

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._create_frames()
        self._create_labels()

        self.gamepk: int = None
        self.delay_seconds: int = 0

        self.data: ScoreboardData = None
        self.diff: ScoreboardData = None

        self._outs_image = None
        self._runners_image = None

    def _create_frames(self):
        self.away_team_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.away_team_frame.place(relx=0.0, rely=0.0,
                                   relwidth=0.22, relheight=0.3)

        self.away_score_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.away_score_frame.place(relx=0.22, rely=0.0,
                                    relwidth=0.16, relheight=0.3)

        self.home_team_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.home_team_frame.place(relx=0.0, rely=0.3,
                                   relwidth=0.22, relheight=0.3)

        self.home_score_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.home_score_frame.place(relx=0.22, rely=0.3,
                                    relwidth=0.16, relheight=0.3)

        self.inning_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.inning_frame.place(relx=0.38, rely=0.0,
                                relwidth=0.16, relheight=0.6)

        self.runners_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.runners_frame.place(relx=0.54, rely=0.0,
                                 relwidth=0.46, relheight=0.7)

        self.outs_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.outs_frame.place(relx=0.54, rely=0.7,
                              relwidth=0.46, relheight=0.3)

        self.status_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.status_frame.place(relx=0.0, rely=0.6,
                                relwidth=0.54, relheight=0.2)

        self.umpire_frame = tk.Frame(self, bd=self._BW, relief='solid')
        self.umpire_frame.place(relx=0.0, rely=0.8,
                                relwidth=0.54, relheight=0.2)

    def _create_labels(self):
        self.away_team = tk.Label(self.away_team_frame, font=self._FONT_BIG)
        self.away_team.place(anchor='w', relx=0.0, rely=0.5)

        self.away_score = tk.Label(self.away_score_frame, font=self._FONT_BIG)
        self.away_score.place(anchor='center', relx=0.5, rely=0.5)

        self.home_team = tk.Label(self.home_team_frame, font=self._FONT_BIG)
        self.home_team.place(anchor='w', relx=0.0, rely=0.5)

        self.home_score =tk.Label(self.home_score_frame, font=self._FONT_BIG)
        self.home_score.place(anchor='center', relx=0.5, rely=0.5)

        self.inning = tk.Label(self.inning_frame, font=self._FONT_BIG)
        self.inning.place(anchor='center', relx=0.5, rely=0.5)

        self.top_inning = tk.Label(self.inning_frame, font=self._ARROW_FONT)
        self.top_inning.place(anchor='n', relx=0.5, rely=0.0)

        self.bot_inning = tk.Label(self.inning_frame, font=self._ARROW_FONT)
        self.bot_inning.place(anchor='s', relx=0.5, rely=1.0)

        self.status = tk.Label(self.status_frame, font=self._FONT_SMALL)
        self.status.place(anchor='w', relx=0.0, rely=0.5)

        self.umpire = tk.Label(self.umpire_frame, font=self._FONT_SMALL)
        self.umpire.place(anchor='w', relx=0.0, rely=0.5)

        self.runners = tk.Label(self.runners_frame, font=self._FONT_BIG)
        self.runners.place(anchor='center', relx=0.5, rely=0.5)

        self.outs = tk.Label(self.outs_frame, image='')
        self.outs.place(anchor='center', relx=0.5, rely=0.5)

    def start(self):
        """
        Starts the game frame. Fetches the data and updates the labels.
        """
        self.data = ScoreboardData(gamepk=self.gamepk,
                                   delay_seconds=self.delay_seconds)

        self._team_labels(self.data.away.abv, self.data.home.abv)
        self._status()

        if 'L' == self.data.game_state: # In Progress
            self._frame_color(self.LIVE_COLOR)
            # Update Scores
            self.away_score.config(text=f'{self.data.away_score}')
            self.home_score.config(text=f'{self.data.home_score}')
            self.inning.config(text=f'{self.data.inning}')
            self.umpire.config(text=f'{self.data.umpire}')
            self._outs(self.data.count.outs)
            self._runners(self.data.runners)
            self._inning_state(self.data.inning_state)
        elif 'P' == self.data.game_state: # Pregame
            self.runners.config(text=f'{self.data.start_time}')
            self._pregame() # Nothing to update. Empty labels
        elif 'F' == self.data.game_state: # Final
            self._frame_color(self.NOT_LIVE_COLOR)
            self.away_score.config(text=f'{self.data.away_score}')
            self.home_score.config(text=f'{self.data.home_score}')
            self.umpire.config(text=f'{self.data.umpire}')
            self.inning.config(text='F')
            self.runners.config(image='')
            self.runners.config(text='')
            self.outs.config(image='')
            self.top_inning.config(text='')
            self.bot_inning.config(text='')
        elif self.data.game_state in ('D', 'S'): # Delayed
            self._frame_color(self.NOT_LIVE_COLOR)
            self.away_score.config(text=f'{self.data.away_score}')
            self.home_score.config(text=f'{self.data.home_score}')
            self.umpire.config(text=f'{self.data.umpire}')
            self._runners(self.data.runners)
            self._outs(self.data.count.outs)

    def fetch_data(self):
        """
        Fetches the updated data from the API and stores the difference in the
        data dictionary. The difference is used to update the labels.
        """
        if self.gamepk is None:
            return

        self.diff = self.data.update_return_difference()

    def update_data(self):
        """
        Updates the labels based on the difference between the current data and
        the updated data. If there is no difference, the labels are not updated.
        """
        if self.gamepk is None:
            self._frame_color(self.NOT_LIVE_COLOR)

        if not self.diff:
            return

        # Update Team Abbreviations
        if self.diff.get('away', None) is not None:
            if self.diff.get('abv', None) is not None:
                self._team_labels(self.data.away.abv, self.data.home.abv)

        if self.diff.get('home', None) is not None:
            if self.diff.get('abv', None) is not None:
                self._team_labels(self.data.away.abv, self.data.home.abv)

        # Update gamepk + codedGameState
        if self.diff.get('gamepk', None) is not None:
            self._status()

        if self.diff.get('game_state', None) is not None:
            self._status()

        self._game_state()

    def _game_state(self):
        if self.data.game_state in 'P':
            self._pregame()
        elif self.data.game_state in ('D', 'S'):
            self._delayed()
        elif self.data.game_state in 'F':
            self._final()
        elif self.data.game_state in 'L':
            self._in_progress()
        else:
            print('Unknown statusCode.')
            print(f'gamepk: {self.data.gamepk}')
            print(f'game_state: {self.data.game_state}')

    def _pregame(self):
        self._frame_color(self.NOT_LIVE_COLOR)
        self.away_score.config(text='')
        self.home_score.config(text='')
        self.inning.config(text='')
        self.top_inning.config(text='')
        self.bot_inning.config(text='')
        self.umpire.config(text='')
        self.outs.config(image='')
        self.runners.config(image='')

        if self.diff:
            if self.diff['start_time'] is not None:
                self.runners.config(text=self.data.start_time)

    def _delayed(self):
        self._frame_color(self.NOT_LIVE_COLOR)
        # Update Scores
        if self.diff.get('away_score', None) is not None:
            self.away_score.config(text=self.data.away_score)
        if self.diff.get('home_score', None) is not None:
            self.home_score.config(text=self.data.home_score)
        if self.diff.get('runners', None) is not None:
            self._runners(self.data.runners)
        if self.diff('umpire', None) is not None:
            self.umpire.config(text=self.data.umpire)

        if self.diff.get('count', None) is not None:
            if self.diff.get('outs', None) is not None:
                self._outs(self.data.count.outs)

    def _final(self):
        self._frame_color(self.NOT_LIVE_COLOR)
        # Update Scores
        if self.diff.get('away_score', None) is not None:
            self.away_score.config(text=self.data.away_score)
        if self.diff.get('home_score', None) is not None:
            self.home_score.config(text=self.data.home_score)
        if self.diff.get('umpire', None) is not None:
            self.umpire.config(text=self.data.umpire)

        if self.diff.get('game_state', None) is not None:
            self.inning.config(text='F')

        self.runners.config(image='')
        self.runners.config(text='')
        self.outs.config(image='')
        self.top_inning.config(text='')
        self.bot_inning.config(text='')

    def _in_progress(self):
        self._frame_color(self.LIVE_COLOR)

        # Update Scores
        if self.diff.get('away_score', None) is not None:
            self.away_score.config(text=f'{self.data.away_score}')
        if self.diff.get('home_score', None) is not None:
            self.home_score.config(text=f'{self.data.home_score}')

        # Update Inning
        if self.diff.get('inning', None) is not None:
            self.inning.config(text=self.data.inning)

        if self.diff.get('inning_state', None) is not None:
            self._inning_state(self.data.inning_state)

        if self.diff.get('umpire', None) is not None:
            self.umpire.config(text=self.data.umpire)

        if self.diff.get('count', None) is not None:
            if self.diff.get('outs', None) is not None:
                self._outs(self.data.count.outs)

        if self.diff.get('runners', None) is not None:
            self._runners(self.data.runners)

    def _status(self):
        text = f'{self.data.gamepk} - {self.data.codedGameState}'
        self.status.config(text=text)

    def _outs(self, outs: int):
        frame_dimension = (117, 45)
        frame_dimension = [int(x * (3/4)) for x in frame_dimension]

        current_dir = os.path.dirname(os.path.relpath(__file__))
        image_folder = os.path.join(current_dir, '..', 'images')
        image_path = os.path.join(image_folder, f'o{outs}.png')

        self._outs_image = Image.open(image_path)
        self._outs_image = self._outs_image.resize(frame_dimension)
        self._outs_image = ImageTk.PhotoImage(self._outs_image)

        self.outs.config(image=self._outs_image)

    def _runners(self, runners: str):
        frame_dimension = (117, 105)
        frame_dimension = [int(x * (.9)) for x in frame_dimension]

        current_dir = os.path.dirname(os.path.relpath(__file__))
        image_folder = os.path.join(current_dir, '..', 'images')
        image_path = os.path.join(image_folder, f'r{runners}.png')

        self._runners_image = Image.open(image_path)
        self._runners_image = self._runners_image.resize(frame_dimension)
        self._runners_image = ImageTk.PhotoImage(self._runners_image)

        self.runners.config(image=self._runners_image)

    def _inning_state(self, inning_state: str):
        if inning_state in ('Top', 'Middle'):
            self.top_inning.config(text='▲')
            self.bot_inning.config(text='')
        elif inning_state in ('Bottom', 'End'):
            self.top_inning.config(text='')
            self.bot_inning.config(text='▼')
        else:
            self.top_inning.config(text='')
            self.bot_inning.config(text='')

    def _team_labels(self, away_team: str, home_team: str):
        self.away_team.config(text=away_team)
        self.home_team.config(text=home_team)

        if away_team in self.RIVAL_TEAMS:
            self.away_team.config(fg=self.RIVAL_COLOR)
            self.away_score.config(fg=self.RIVAL_COLOR)
            self.top_inning.config(fg=self.RIVAL_COLOR)
        if home_team in self.RIVAL_TEAMS:
            self.home_team.config(fg=self.RIVAL_COLOR)
            self.home_score.config(fg=self.RIVAL_COLOR)
            self.bot_inning.config(fg=self.RIVAL_COLOR)

        if away_team in self.BET_TEAMS:
            self.away_team.config(fg=self.BET_COLOR)
            self.away_score.config(fg=self.BET_COLOR)
            self.top_inning.config(fg=self.BET_COLOR)
        if home_team in self.BET_TEAMS:
            self.home_team.config(fg=self.BET_COLOR)
            self.home_score.config(fg=self.BET_COLOR)
            self.bot_inning.config(fg=self.BET_COLOR)

        if away_team in self.FAV_TEAMS:
            self.away_team.config(fg=self.FAV_COLOR)
            self.away_score.config(fg=self.FAV_COLOR)
            self.top_inning.config(fg=self.FAV_COLOR)
        if home_team in self.FAV_TEAMS:
            self.home_team.config(fg=self.FAV_COLOR)
            self.home_score.config(fg=self.FAV_COLOR)
            self.bot_inning.config(fg=self.FAV_COLOR)

    def _frame_color(self, bg_color: str):
        # Frames
        self.config(bg=bg_color)
        self.away_team_frame.config(bg=bg_color)
        self.home_team_frame.config(bg=bg_color)
        self.away_score_frame.config(bg=bg_color)
        self.home_score_frame.config(bg=bg_color)
        self.inning_frame.config(bg=bg_color)
        self.runners_frame.config(bg=bg_color)
        self.outs_frame.config(bg=bg_color)
        self.status_frame.config(bg=bg_color)
        self.umpire_frame.config(bg=bg_color)

        # Labels
        self.away_team.config(bg=bg_color)
        self.home_team.config(bg=bg_color)
        self.away_score.config(bg=bg_color)
        self.home_score.config(bg=bg_color)
        self.inning.config(bg=bg_color)
        self.top_inning.config(bg=bg_color)
        self.bot_inning.config(bg=bg_color)
        self.runners.config(bg=bg_color)
        self.outs.config(bg=bg_color)
        self.status.config(bg=bg_color)
        self.umpire.config(bg=bg_color)

class TimeFrame(tk.Frame):
    """
    TimeFrame class is a frame that displays the current time and date.
    """
    _BOARDER_WIDTH = 0
    _BW = _BOARDER_WIDTH

    _BACKGROUND_COLOR = GameFrame.NOT_LIVE_COLOR
    _BG = _BACKGROUND_COLOR

    _FONT = ('Consolas', 22, 'bold')
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.delay_seconds = 0

        self.top_frame = tk.Frame(self, bd=self._BW,
                                  relief='solid', bg=self._BG)
        self.top_frame.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.5)

        self.bot_frame = tk.Frame(self, bd=self._BW,
                                  relief='solid', bg=self._BG)
        self.bot_frame.place(relx=0.0, rely=0.5, relwidth=1.0, relheight=0.5)

        self.date = tk.Label(self.top_frame, text='',
                             font=self._FONT, bg=self._BG)
        self.date.place(anchor='s', relx=0.5, rely=1.0)

        self.time = tk.Label(self.bot_frame, text='',
                             font=self._FONT, bg=self._BG)
        self.time.place(anchor='n', relx=0.5, rely=0.0)

    def update(self):
        """Updates the time and date labels"""
        date, time = self.time_seconds_ago()
        self.date.config(text=date)
        self.time.config(text=time)

    def time_seconds_ago(self) -> Tuple[str, str]:
        """
        Returns the date and time from a given number of seconds ago.
        Date is ISO8601 format and time is in 12 hour format.

        Returns:
            Tuple[str, str]: date and time in the format:
                (YYYY-MM-DD, HH:MM:SS AM/PM)
        """
        now = datetime.now()
        delayed = now - timedelta(seconds=self.delay_seconds)

        full_iso = delayed.isoformat()
        date = full_iso[:10]
        time = delayed.strftime('%I:%M:%S %p')

        if time[0] == '0':
            time = time[1:]

        return (date, time)

class Scoreboard:
    """
    Scoreboard class is the main class that creates the GUI for the MLB
    scoreboard. The scoreboard displays the current games being played and the
    current time and date.
    """
    def __init__(self, delay_seconds: int = 0, date: str = None):
        self.delay_seconds = delay_seconds

        self.update_games_lock = threading.Lock()
        self.update_time_lock = threading.Lock()

        self.update_games_thread = threading.Thread(target=self._fetch_game_data)

        self.window = tk.Tk()
        self.window.title('MLB Scoreboard')
        self.window.geometry('1024x600')

        self.gamepks: List[int] = get_daily_gamepks(date=date)

        if len(self.gamepks) > 16:
            self.gamepks = self.gamepks[:16]

        if len(self.gamepks) < 16:
            self.max_games: bool = True
            self.time_frame: TimeFrame = TimeFrame(master=self.window, bd=1, relief='solid')
            self.time_frame.delay_seconds = self.delay_seconds

            self.time_frame.grid(row=3, column=3, padx=0, pady=0, sticky='nsew')
        else:
            self.max_games: bool = False
            self.time_frame: TimeFrame = None

        self.game_frames: List[GameFrame] = []

        for i, gamepk in enumerate(self.gamepks):
            row, col = divmod(i, 4)
            gameframe = GameFrame(self.window, bd=1, relief='solid')
            gameframe.gamepk = gamepk
            gameframe.delay_seconds = self.delay_seconds
            gameframe.start()

            self.game_frames.append(gameframe)
            self.game_frames[i].grid(row=row, column=col,
                                     padx=0, pady=0,sticky='nsew')

        while len(self.game_frames) < 15:
            i = len(self.game_frames)
            row, col = divmod(i, 4)
            self.game_frames.append(GameFrame(self.window, bd=1, relief='solid'))
            self.game_frames[-1].grid(row=row, column=col, padx=0, pady=0, sticky='nsew')

        for i in range(4):
            self.window.grid_columnconfigure(i, weight=1)
            self.window.grid_rowconfigure(i, weight=1)

        self._game_timer()
        self._time_timer()

        self.window.mainloop()

    def _game_timer(self):
        if not self.update_games_thread.is_alive():
            self.update_games_thread = threading.Thread(target=self._fetch_game_data)
            self.update_games_thread.start()
        self._update_games()
        self.window.after(5000, self._game_timer)

    def _fetch_game_data(self):
        for game_frame in self.game_frames:
            game_frame.fetch_data()

    def _update_games(self):
        for game_frame in self.game_frames:
            game_frame.update_data()

    def _time_timer(self):
        if self.time_frame is not None:
            with self.update_time_lock:
                self._update_time()
                self.window.after(100, self._time_timer)

    def _update_time(self):
        self.time_frame.update()

def main():
    """
    Main function that creates the GUI for the MLB scoreboard.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=int, default=60,
                        help='Delay in seconds')

    parser.add_argument('--date', type=str, default=None,
                        help='Date in ISO8601 format')

    # args = parser.parse_args()

    Scoreboard(delay_seconds=60, date=None)

if __name__ == '__main__':
    main()
