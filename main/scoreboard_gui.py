from datetime import datetime, timedelta
from typing import List
import tkinter as tk
import threading
from get.game import Game
from get.umpire import Umpire
from get.runners import Runners
from get.statsapi_plus import get_daily_gamePks

class GameFrame(tk.Frame):
    _FRAME_BORDER = 0
    _FB = _FRAME_BORDER

    _FONT_BIG = ('Consolas', 22, 'bold')
    _FONT_SMALL = ('Consolas', 12)

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.away_team_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.away_team_frame.place(relx=0.0, rely=0.0, relwidth=0.22, relheight=0.3)

        self.away_name = tk.Label(self.away_team_frame, text='', font=self._FONT_BIG)
        self.away_name.place(anchor='w', relx=0.0, rely=0.5)


        self.home_team_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.home_team_frame.place(relx=0.0, rely=0.3, relwidth=0.22, relheight=0.3)

        self.home_name = tk.Label(self.home_team_frame, text='', font=self._FONT_BIG)
        self.home_name.place(anchor='w', relx=0.0, rely=0.5)


        self.away_score_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.away_score_frame.place(relx=0.22, rely=0.0, relwidth=0.16, relheight=0.3)

        self.away_score = tk.Label(self.away_score_frame, text='', font=self._FONT_BIG)
        self.away_score.place(anchor='center', relx=0.5, rely=0.5)


        self.home_score_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.home_score_frame.place(relx=0.22, rely=0.3, relwidth=0.16, relheight=0.3)

        self.home_score = tk.Label(self.home_score_frame, text='', font=self._FONT_BIG)
        self.home_score.place(anchor='center', relx=0.5, rely=0.5)


        self.inning_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.inning_frame.place(relx=0.38, rely=0.0, relwidth=0.16, relheight=0.6)

        self.inning = tk.Label(self.inning_frame, text='', font=self._FONT_BIG)
        self.inning.place(anchor='center', relx=0.5, rely=0.5)

        self.top_inning = tk.Label(self.inning_frame, text='', font=('Consolas', 18, 'bold'))
        self.top_inning.place(anchor='n', relx=0.5, rely=0)

        self.bot_inning = tk.Label(self.inning_frame, text='', font=('Consolas', 18, 'bold'))
        self.bot_inning.place(anchor='s', relx=0.5, rely=1)


        self.gamepk_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.gamepk_frame.place(relx=0.0, rely=0.6, relwidth=0.54, relheight=0.2)

        self.gamepk = tk.Label(self.gamepk_frame, text='', font=self._FONT_SMALL)
        self.gamepk.place(anchor='w', relx=0, rely=0.5)


        self.umpire_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.umpire_frame.place(relx=0.0, rely=0.8, relwidth=0.54, relheight=0.2)

        self.umpire = tk.Label(self.umpire_frame, text='', font=self._FONT_SMALL)
        self.umpire.place(anchor='w', relx=0.0, rely=0.5)


        self.runners_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.runners_frame.place(relx=0.54, rely=0.0, relwidth=0.46, relheight=0.7)

        self.runners = tk.Label(self.runners_frame, text='', font=self._FONT_BIG)
        self.runners.place(anchor='center', relx=0.5, rely=0.5)


        self.outs_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.outs_frame.place(relx=0.54, rely=0.7, relwidth=0.46, relheight=0.3)

        self.outs = tk.Label(self.outs_frame, text='', font=self._FONT_BIG)
        self.outs.place(anchor='center', relx=0.5, rely=0.5)

    def update_from_gamepk(self, gamePk:int, delay_seconds: int = 0):

        game: Game = Game.get_game_from_pk(gamePk, delay_seconds=delay_seconds)

        # Team Abbreviations
        self.away_name.config(text=game.gameData.teams.away.abbreviation)
        self.home_name.config(text=game.gameData.teams.home.abbreviation)

        # Scores
        self.away_score.config(text=game.liveData.linescore.teams.away.runs)
        self.home_score.config(text=game.liveData.linescore.teams.home.runs)

        # gamePk + Umpire
        self.gamepk.config(text=f'pk = {game.gamePk}')

        # Live / In Progress
        if game.gameData.status.abstractGameState in ('Live', 'In Progress'):
            self._live_game(game)

        # Scheduled / Pre-Game
        elif game.gameData.status.detailedState in ('Scheduled', 'Pre-Game', 'Warmup', 'Preview'):
            self._pregame(game)
            self.umpire.config(text='')

        # Final / Game Over
        elif game.gameData.status.detailedState in ('Final', 'Game Over'):
            self._completed_game(game)

        # Q: Should I use detailed or abstract game states?


        # How do you know all the possible values for detailedState?
        # print(set([game.gameData.status.detailedState for game in games]))

    def _pregame(self, game: Game):
        self.outs.config(text='')
        self.inning.config(text='')
        self.runners.config(text=game.gameData.datetime.startTime)

    def _live_game(self, game: Game):
        monte = Umpire.delta_favor_monte
        umpire: Umpire = Umpire(game=game)
        umpire.calculate(delta_favor_func=monte)

        # Runners
        runners = Runners()
        runners.set_bases_offense(game.liveData.linescore.offense)
        self.runners.config(text=repr(runners))

        # Umpire
        self.umpire.config(text=f'{str(umpire)} ({int(umpire)})')

        # Outs
        outs = game.liveData.linescore.outs
        if outs == 1:
            self.outs.config(text='1 Out')
        else:
            self.outs.config(text=f'{outs} Outs')

        # Inning State
        if game.liveData.linescore.inningState in ('Top', 'Middle'):
            self.top_inning.config(text='•')
            self.bot_inning.config(text='')
        elif game.liveData.linescore.inningState in ('Bottom', 'End'):
            self.top_inning.config(text='')
            self.bot_inning.config(text='•')

        # Inning logic
        # self.inning.config(text='13')
        self.inning.config(text=game.liveData.linescore.currentInning)

    def _completed_game(self, game: Game):
        monte = Umpire.delta_favor_monte
        umpire: Umpire = Umpire(game=game)
        umpire.calculate(delta_favor_func=monte)

        self.umpire.config(text=f'{str(umpire)} ({int(umpire)})')

        self.runners.config(text='')
        self.outs.config(text='')
        self.inning.config(text='F')
        self.bot_inning.config(text='')
        self.top_inning.config(text='')

    def clear_frame(self):
        """Clears all labels in the frame"""
        self.away_name.config(text='')
        self.home_name.config(text='')
        self.away_score.config(text='')
        self.home_score.config(text='')
        self.gamepk.config(text='')
        self.umpire.config(text='')
        self.runners.config(text='')
        self.outs.config(text='')

class TimeFrame(tk.Frame):
    _FRAME_BORDER = 0
    _FB = _FRAME_BORDER

    _FONT_BIG = ('Consolas', 22, 'bold')
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.top_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.top_frame.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.5)

        self.bot_frame = tk.Frame(self, bd=self._FB, relief='solid')
        self.bot_frame.place(relx=0.0, rely=0.5, relwidth=1.0, relheight=0.5)

        self.date = tk.Label(self.top_frame, text='', font=self._FONT_BIG)
        self.date.place(anchor='s', relx=0.5, rely=1.0)

        self.time = tk.Label(self.bot_frame, text='', font=self._FONT_BIG)
        self.time.place(anchor='n', relx=0.5, rely=0.0)

    def abcdef(self, delay_seconds: int = 0):
        date, time = self._time_seconds_ago(delay_seconds)

        self.date.config(text=date)
        self.time.config(text=time)

    def _time_seconds_ago(self, delay_seconds: int):
        # Fetch the current local time
        now = datetime.now()

        # Subtract the given number of seconds to get the time from x seconds ago
        delayed = now - timedelta(seconds=delay_seconds)

        delay_date = delayed.isoformat()[:10]

        # Format the resulting time
        delay_time = delayed.strftime('%I:%M:%S %p')

        if delay_time[0] == '0':
            delay_time = delay_time[1:]

        return (delay_date, delay_time)

class GUI:
    def __init__(self, update_timer_seconds:int = 0, delay_seconds: int = 0):
        self.window = tk.Tk()
        self.window.geometry('1024x600')
        self.window.title('GUI Test')

        self.update_timer_seconds: int = update_timer_seconds
        self.delay_seconds: int = delay_seconds

        self.gamePks = get_daily_gamePks()

        while len(self.gamePks) < 15:
            self.gamePks.append(None)

        self.frames: List[tk.Frame] = []
        self.time_frame = TimeFrame(self.window, bd=1, relief='solid')

        # Create 16 frames and place them in a 4x4 grid
        for _ in self.gamePks:
            self.frames.append(GameFrame(self.window, bd=1, relief='solid'))

        # Place frames in grid
        for index, frame in enumerate(self.frames):
            row, col = divmod(index, 4)
            frame.grid(row=row, column=col, padx=0, pady=0, sticky='nsew')

            # Ensure grid cells expand to fill window with resize event
            self.window.grid_rowconfigure(row, weight=1)
            self.window.grid_columnconfigure(col, weight=1)

        if len(self.frames) < 16:
            self.time_frame.grid(row=3, column=3, padx=0, pady=0, sticky='nsew')
            self.window.grid_rowconfigure(3, weight=1)
            self.window.grid_columnconfigure(3, weight=1)

        self._update_game_frames()
        self._update_time_frame()

        # Start Window
        self.window.mainloop()

    def _update_game_frames(self):
        update_game_thread = threading.Thread(target=self._update_indvidual_frames)
        update_game_thread.start()
        self.window.after(self.update_timer_seconds * 1000, self._update_game_frames)

    def _update_indvidual_frames(self):
        for frame, gamePk in zip(self.frames, self.gamePks):
            if gamePk is None:
                frame.clear_frame()
            else:
                frame.update_from_gamepk(gamePk, self.delay_seconds)

    def _update_time_frame(self):
        update_time_thread = threading.Thread(target=self._update_time)
        update_time_thread.start()
        self.window.after(1000, self._update_time_frame)

    def _update_time(self):
        self.time_frame.abcdef(self.delay_seconds)

if __name__ == '__main__':
    gui = GUI(update_timer_seconds=10, delay_seconds=60)
