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

    _NOT_LIVE_COLOR = '#0162FF'
    _LIVE_COLOR = '#02CEFE'

    known_statusCodes = ('S', 'P', 'PR', 'PW', 'I', 'MF', 'MA', 'NH', 'IO',
                         'IR', 'TR', 'UR', 'O', 'F')

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
        self._gamePk = get_daily_gamePks
        self._delay_seconds = delay_seconds

        game: Game = Game.get_game_from_pk(gamePk, delay_seconds=delay_seconds)
        abstractGameState = game.gameData.status.abstractGameState
        abstractGameCode = game.gameData.status.abstractGameCode
        detailedState = game.gameData.status.detailedState
        codedGameState = game.gameData.status.codedGameState
        statusCode = game.gameData.status.statusCode

        # Team Abbreviations
        self.away_name.config(text=game.gameData.teams.away.abbreviation)
        self.home_name.config(text=game.gameData.teams.home.abbreviation)

        # gamePk + Umpire
        self.gamepk.config(text=f'pk = {game.gamePk}')

        # Pre-Game
        if codedGameState in ('S', 'P'):
            self._pregame(game)

        # Final / Game Over
        elif codedGameState in ('O', 'F'):
            self._completed_game(game)

        # Delayed
        elif 'Delayed' in detailedState:
            self._delayed(game)

        # Suspended
        elif 'Suspended' in detailedState:
            self._suspended(game)

        # Live / In Progress
        elif codedGameState in ('I', 'M', 'N'):
            self._live_game(game)

        # Other
        if statusCode not in self.known_statusCodes:
            self._unknown(game)

    def _pregame(self, game: Game):
        self._frame_bg(self._NOT_LIVE_COLOR)
        self.umpire.config(text='')
        self.away_score.config(text='')
        self.home_score.config(text='')
        self.outs.config(text='')
        self.inning.config(text='')
        self.umpire.config(text='')
        self.runners.config(text=game.gameData.datetime.startTime)

    def _completed_game(self, game: Game):
        self._frame_bg(self._NOT_LIVE_COLOR)

        self._umpire(game)
        self._scores(game)
        self.runners.config(text='')
        self.outs.config(text='')
        self.inning.config(text='F')
        self.bot_inning.config(text='')
        self.top_inning.config(text='')

    def _delayed(self, game: Game):
        self._frame_bg(self._NOT_LIVE_COLOR)
        self.inning.config(text=game.liveData.linescore.currentInning)
        self.runners.config(text='Delay')
        self._outs(game)
        self._inning_state(game)
        self._umpire(game)
        self._scores(game)

    def _suspended(self, game: Game):
        self._frame_bg(self._NOT_LIVE_COLOR)
        self.inning.config(text=game.liveData.linescore.currentInning)
        self.runners.config(text='Susp')
        self._outs(game)
        self._inning_state(game)
        self._umpire(game)
        self._scores(game)

    def _live_game(self, game: Game):
        self._frame_bg(self._LIVE_COLOR)
        self._umpire(game)
        self._runners(game)
        self._outs(game)
        self._inning_state(game)
        self._scores(game)
        self.inning.config(text=game.liveData.linescore.currentInning)

    def _unknown(self, game: Game):
        abstractGameState = game.gameData.status.abstractGameState
        abstractGameCode = game.gameData.status.abstractGameCode
        detailedState = game.gameData.status.detailedState
        codedGameState = game.gameData.status.codedGameState

        time = time_seconds_ago(delay_seconds=self._delay_seconds)
        gamepk = game.gamePk

        print()
        print(f'gamepk: {gamepk}')
        print(f'time: {time}')
        print(f'abstractGameState: {abstractGameState}')
        print(f'abstractGameCode: {abstractGameCode}')
        print(f'detailedState: {detailedState}')
        print(f'codedGameState: {codedGameState}')

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

    def _frame_bg(self, bg_color: str):
        if bg_color == 'dark blue':
            bg_color = '#0056c0'
        elif bg_color == 'light blue':
            bg_color = '#029EFE'

        self.away_team_frame.config(bg=bg_color)
        self.home_team_frame.config(bg=bg_color)
        self.away_score_frame.config(bg=bg_color)
        self.home_score_frame.config(bg=bg_color)
        self.inning_frame.config(bg=bg_color)
        self.gamepk_frame.config(bg=bg_color)
        self.umpire_frame.config(bg=bg_color)
        self.runners_frame.config(bg=bg_color)
        self.outs_frame.config(bg=bg_color)

        self.away_name.config(bg=bg_color)
        self.home_name.config(bg=bg_color)
        self.away_score.config(bg=bg_color)
        self.home_score.config(bg=bg_color)
        self.inning.config(bg=bg_color)
        self.gamepk.config(bg=bg_color)
        self.umpire.config(bg=bg_color)
        self.runners.config(bg=bg_color)
        self.outs.config(bg=bg_color)
        self.top_inning.config(bg=bg_color)
        self.bot_inning.config(bg=bg_color)

        pass

    def _outs(self, game: Game):
        # Outs
        outs = game.liveData.linescore.outs
        if outs == 1:
            self.outs.config(text='1 Out')
        else:
            self.outs.config(text=f'{outs} Outs')

    def _runners(self, game: Game):
        runners = Runners()
        runners.set_bases_offense(game.liveData.linescore.offense)
        self.runners.config(text=repr(runners))

    def _umpire(self, game: Game):
        monte = Umpire.delta_favor_monte

        umpire: Umpire = Umpire(game=game)
        umpire.calculate(delta_favor_func=monte)
        self.umpire.config(text=f'{str(umpire)} ({int(umpire)})')

    def _inning_state(self, game: Game):
        # Inning State
        if game.liveData.linescore.inningState in ('Top', 'Middle'):
            self.top_inning.config(text='•')
            self.bot_inning.config(text='')
        elif game.liveData.linescore.inningState in ('Bottom', 'End'):
            self.top_inning.config(text='')
            self.bot_inning.config(text='•')

    def _scores(self, game: Game):
        self.away_score.config(text=game.liveData.linescore.teams.away.runs)
        self.home_score.config(text=game.liveData.linescore.teams.home.runs)

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
        date, time = time_seconds_ago(delay_seconds)

        self.date.config(text=date)
        self.time.config(text=time)

def time_seconds_ago(delay_seconds: int):
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
    gui = GUI(update_timer_seconds=10, delay_seconds=0)
