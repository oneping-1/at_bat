import os
from datetime import datetime, timedelta
from typing import List, Tuple
import argparse
import tkinter as tk
import threading
import copy
from PIL import Image, ImageTk
from get.statsapi_plus import get_daily_gamepks
from get.game import Game
from get.runners import Runners
from get.umpire import Umpire


class ScoreboardData:
    def __init__(self, gamepk: int, delay_seconds: int = 0):
        self.gamepk = gamepk
        self.delay_seconds = delay_seconds
        self.get_data()

    def get_data(self):
        self.game = Game.get_game_from_pk(gamepk=self.gamepk,
                                          delay_seconds=self.delay_seconds)

        self.abstractGameState = self.game.gameData.status.abstractGameState
        self.abstractGameCode = self.game.gameData.status.abstractGameCode
        self.detailedState = self.game.gameData.status.detailedState
        self.codedGameState = self.game.gameData.status.codedGameState
        self.statusCode = self.game.gameData.status.statusCode

        self.start_time = self.game.gameData.datetime.startTime

        self.away_team: str = self.game.gameData.teams.away.abbreviation
        self.home_team: str = self.game.gameData.teams.home.abbreviation

        self.away_score: int = self.game.liveData.linescore.teams.away.runs
        self.home_score: int = self.game.liveData.linescore.teams.home.runs

        self.inning: int = self.game.liveData.linescore.currentInning

        # inningState: 'Top', 'Middle', 'Bottom', 'End'
        self.inningState: str = self.game.liveData.linescore.inningState

        self.outs: int = self.game.liveData.linescore.outs

        self.runners = Runners()
        self.runners.set_bases_offense(self.game.liveData.linescore.offense)
        self.runners: str = repr(self.runners)

        self.umpire = Umpire(gamepk=self.gamepk,
                             delay_seconds=self.delay_seconds)

        self.umpire.calculate(delta_favor_func=Umpire.delta_favor_monte)
        self.umpire = f'{repr(self.umpire)} ({self.umpire.num_missed_calls})'

    def copy(self):
        return copy.deepcopy(self)

    @classmethod
    def diff(cls, old: 'ScoreboardData', new: 'ScoreboardData'
                         ) -> 'ScoreboardData':

        if old is None and new is None:
            return None
        if old is None and new is not None:
            return new.copy()
        if old is not None and new is None:
            return None

        differences = new.copy()

        if old.gamepk == new.gamepk:
            differences.gamepk = None

        if old.abstractGameState == new.abstractGameState:
            differences.abstractGameState = None

        if old.abstractGameCode == new.abstractGameCode:
            differences.abstractGameCode = None

        if old.detailedState == new.detailedState:
            differences.detailedState = None

        if old.codedGameState == new.codedGameState:
            differences.codedGameState = None

        if old.statusCode == new.statusCode:
            differences.statusCode = None

        if old.start_time == new.start_time:
            differences.start_time = None

        if old.away_team == new.away_team:
            differences.away_team = None

        if old.home_team == new.home_team:
            differences.home_team = None

        if old.away_score == new.away_score:
            differences.away_score = None

        if old.home_score == new.home_score:
            differences.home_score = None

        if old.inning == new.inning:
            differences.inning = None

        if old.inningState == new.inningState:
            differences.inningState = None

        if old.outs == new.outs:
            differences.outs = None

        if old.runners == new.runners:
            differences.runners = None

        if old.umpire == new.umpire:
            differences.umpire = None

        return differences

class GameFrame(tk.Frame):
    _BOARDER_WIDTH = 0
    _BW = _BOARDER_WIDTH

    _FONT_BIG = ('Consolas', 22, 'bold')
    _FONT_SMALL = ('Consolas', 12, 'bold')
    _ARROW_FONT = ('Consolas', 18, 'bold')

    LIVE_COLOR = 'white'
    NOT_LIVE_COLOR = 'light grey'

    RIVAL_TEAMS = 'HOU'
    RIVAL_COLOR = 'firebrick1'
    FAV_TEAMS = 'TEX'
    FAV_COLOR = 'blue'
    BET_TEAMS = ()
    BET_COLOR = 'green'

    # I could read these from game states.xlsx but ¯\_(ツ)_/¯
    KNOWN_STATUSCODES = ('S', 'P', 'PR', 'PY', 'PW', 'I', 'IO', 'IR', 'MA',
                         'MC', 'ME', 'MF', 'MG', 'MI', 'MP', 'MT', 'MU', 'MV',
                         'NF', 'NH', 'TR', 'UR', 'O', 'OR', 'F', 'FR', 'DR',
                         'DI')

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._create_frames()
        self._create_labels()

        self.gamepk: int = None
        self._delay_seconds: int = 0

        self.new_data: ScoreboardData = None
        self.old_data: ScoreboardData = None
        self.diff: ScoreboardData = None

        self._outs_image = None
        self._runners_image = None

        self.old_data: ScoreboardData = None
        self.new_data: ScoreboardData = None

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

    def fetch_data(self):
        if self.gamepk is None:
            return

        if self.new_data is None:
            self.old_data = None
        else:
            self.old_data: ScoreboardData = self.new_data.copy()
        self.new_data: ScoreboardData = ScoreboardData(gamepk=self.gamepk,
                                       delay_seconds=self._delay_seconds)

        self.diff: ScoreboardData = ScoreboardData.diff(old=self.old_data,
                                                        new=self.new_data)

        if self.new_data.statusCode not in self.KNOWN_STATUSCODES:
            self._unknown_statuscode()

    def update_data(self):
        if self.gamepk is None:
            self._frame_color(self.NOT_LIVE_COLOR)

        if self.diff is None:
            return

        # Update Team Abbreviations
        if self.diff.away_team is not None or self.diff.home_team is not None:
            self._team_labels(self.diff.away_team, self.diff.home_team)

        # Update gamepk + codedGameState
        if self.diff.gamepk is not None or self.diff.codedGameState is not None:
            self._status()

        # Pregame
        if self.new_data.codedGameState in ('S', 'P'):
            self._pregame()

        # Delay
        elif 'Delay' in self.new_data.detailedState:
            self._delayed()

        # Suspended
        elif self.new_data.codedGameState in ('T', 'U'):
            self._delayed()
            # might make seperate suspended function?

        # Final
        elif self.new_data.codedGameState in ('F', 'O'):
            self._final()

        # Just Started
        elif (self.old_data is not None and self.new_data is not None and self.old_data.codedGameState == 'P' and self.new_data.codedGameState == 'I'):
            self._just_started()

        # In Progress
        elif self.new_data.codedGameState in ('I', 'M', 'N'):
            self._in_progress()

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

        if self.diff.start_time is not None:
            self.runners.config(text=self.diff.start_time)

    def _delayed(self):
        self._frame_color(self.NOT_LIVE_COLOR)
        # Update Scores
        if self.diff.away_score is not None:
            self.away_score.config(text=self.diff.away_score)
        if self.diff.home_score is not None:
            self.home_score.config(text=self.diff.home_score)
        if self.diff.runners is not None:
            self._runners(self.diff.runners)
        if self.diff.outs is not None:
            self._outs(self.diff.outs)
        if self.diff.umpire is not None:
            self.umpire.config(text=self.diff.umpire)

        if self.diff.outs is not None:
            self._outs(self.diff.outs)

    def _final(self):
        self._frame_color(self.NOT_LIVE_COLOR)
        # Update Scores
        if self.diff.away_score is not None:
            self.away_score.config(text=self.diff.away_score)
        if self.diff.home_score is not None:
            self.home_score.config(text=self.diff.home_score)
        if self.diff.umpire is not None:
            self.umpire.config(text=self.diff.umpire)

        self.inning.config(text='F')
        self.runners.config(image='')
        self.runners.config(text='')
        self.outs.config(image='')
        self.top_inning.config(text='')
        self.bot_inning.config(text='')

    def _just_started(self):
        self._frame_color(self.LIVE_COLOR)
        # Update Scores
        self.away_score.config(text=f'{self.new_data.away_score}')
        self.home_score.config(text=f'{self.new_data.home_score}')

        self.inning.config(text=f'{self.new_data.inning}')
        self.umpire.config(text=f'{self.new_data.umpire}')

        self._outs(self.new_data.outs)
        self._runners(self.new_data.runners)
        self._inning_state(self.new_data.inningState)

    def _in_progress(self):
        self._frame_color(self.LIVE_COLOR)
        # Update Scores
        if self.diff.away_score is not None:
            self.away_score.config(text=f'{self.new_data.away_score}')
        if self.diff.home_score is not None:
            self.home_score.config(text=f'{self.new_data.home_score}')

        # Update Inning
        if self.diff.inning is not None:
            self.inning.config(text=self.new_data.inning)

        if self.diff.umpire is not None:
            self.umpire.config(text=self.new_data.umpire)

        if self.diff.outs is not None:
            self._outs(self.new_data.outs)

        if self.diff.runners is not None:
            self._runners(self.new_data.runners)

        if self.diff.inningState is not None:
            self._inning_state(self.new_data.inningState)

    def _status(self):
        text = f'{self.new_data.gamepk} - {self.new_data.codedGameState}'
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

    def _unknown_statuscode(self):
        current_dir = os.path.dirname(os.path.relpath(__file__))
        csv_folder = os.path.join(current_dir, '..', 'csv')
        path = os.path.join(csv_folder, 'unknown_statusCodes.txt')

        now = datetime.now()
        time = now.isoformat()

        data: ScoreboardData = self.new_data

        with open(path, 'a', encoding='utf-8') as file:
            file.write(f'gamepk: {self.new_data.gamepk}\n')
            file.write(f'time: {time}\n')
            file.write(f'astractGameState: {data.abstractGameState}\n')
            file.write(f'abstractGameCode: {data.abstractGameCode}\n')
            file.write(f'detailedState: {data.detailedState}\n')
            file.write(f'codedGameState: {data.codedGameState}\n')
            file.write(f'statusCode: {data.statusCode}\n')
            file.write('\n')

        print(f'gamepk: {self.new_data.gamepk}')
        print(f'time: {time}')
        print(f'astractGameState: {data.abstractGameState}')
        print(f'abstractGameCode: {data.abstractGameCode}')
        print(f'detailedState: {data.detailedState}')
        print(f'codedGameState: {data.codedGameState}')
        print(f'statusCode: {data.statusCode}')
        print('\n')

    @property
    def delay_seconds(self):
        return self._delay_seconds

    @delay_seconds.setter
    def delay_seconds(self, delay_seconds: int):
        if delay_seconds < 0:
            raise ValueError('delay_seconds must be greater than 0')
        self._delay_seconds = round(delay_seconds)

class TimeFrame(tk.Frame):
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
            self.game_frames.append(GameFrame(self.window, bd=1, relief='solid'))

            self.game_frames[i].gamepk = gamepk
            self.game_frames[i].delay_seconds = self.delay_seconds
            self.game_frames[i].grid(row=row, column=col, padx=0, pady=0, sticky='nsew')

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
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=int, default=60,
                        help='Delay in seconds')

    parser.add_argument('--date', type=str, default=None,
                        help='Date in ISO8601 format')

    args = parser.parse_args()

    Scoreboard(delay_seconds=args.delay, date=args.date)

if __name__ == '__main__':
    main()
