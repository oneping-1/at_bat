import tkinter as tk
from get import game as gm, Game
from typing import List
import sys
import time
from tqdm import tqdm

background = 'blue'
font_size = 12

class Scoreboard:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Scoreboard')

        self.main_frame = tk.Frame(self.window, bg=background)
        self.main_frame.pack()

    def create_game_frames(self):
        self.game_frames = []
        for _ in self.games:
            self.game_frames.append(tk.Frame(self.main_frame, bg=background))

    def display_game_frames(self):

        for i,frame in enumerate(self.game_frames):
            game = self.games[i]
            ac, hc = self.get_colors(game) # awah/home colors

            team_abv = ['away', 'home'] # [Away, Home]
            scorebox = ['', '', '', ''] # Scorebox [1, 2; 3, 4]

            team_abv[0] = game.gameData.teams.away.abbreviation
            team_abv[1] = game.gameData.teams.home.abbreviation

            if len(team_abv[0]) == 2:
                team_abv[0] += ' '
            if len(team_abv[1]) == 2:
                team_abv[1] += ' '

            if 'Delay' in game.gameData.status.detailedState:
                scorebox[0] = f'{game.liveData.linescore.teams.away.runs}'
                scorebox[2] = f'{game.liveData.linescore.teams.home.runs}'
                scorebox[1] = 'DL'
                scorebox[3] = f'{game.liveData.linescore.currentInning}'
            elif 'Preview' in game.gameData.status.abstractGameState or 'Warmup' in game.gameData.status.detailedState:
                scorebox[0] = f'{game.gameData.datetime.startHour}'
                scorebox[1] = f'{game.gameData.datetime.startMin}'
            elif 'Final' in game.gameData.status.abstractGameState:
                scorebox[0] = f'{game.liveData.linescore.teams.away.runs}'
                scorebox[2] = f'{game.liveData.linescore.teams.home.runs}'
                scorebox[1] = 'F'
                if game.liveData.linescore.currentInning != 9:
                    scorebox[3] = f'{game.liveData.linescore.currentInning}'
            else:
                scorebox[0] = f'{game.liveData.linescore.teams.away.runs}'
                scorebox[2] = f'{game.liveData.linescore.teams.home.runs}'
                scorebox[1] = f'o{game.liveData.linescore.outs}'
                scorebox[3] = f'{game.liveData.linescore.currentInning}'

                if 'Top' in game.liveData.linescore.inningState or 'Mid' in game.liveData.linescore.inningState:
                    team_abv[0] += '-'
                elif 'Bot' in game.liveData.linescore.inningState or 'End' in game.liveData.linescore.inningState:
                    team_abv[1] += '-'

            frame.pack(pady=4)

            away_team = tk.Label(frame, text=f'{team_abv[0]:<4s}', font=('DSEG14 Classic', font_size), fg=ac, bg='black')
            away_team.grid(row=0, column=0)

            home_team = tk.Label(frame, text=f'{team_abv[1]:<4s}', font=('DSEG14 Classic', font_size), fg=hc, bg='black')
            home_team.grid(row=1, column=0)

            scorebox1 = tk.Label(frame, text=f'{scorebox[0]:>2s}', font=('DSEG7 Classic', font_size), fg=ac, bg='black')
            scorebox1.grid(row=0, column=1,padx=2)

            scorebox2 = tk.Label(frame, text=f'{scorebox[1]:>2s}', font=('DSEG7 Classic', font_size), fg=ac, bg='black')
            scorebox2.grid(row=0, column=2)

            scorebox3 = tk.Label(frame, text=f'{scorebox[2]:>2s}', font=('DSEG7 Classic', font_size), fg=hc, bg='black')
            scorebox3.grid(row=1, column=1,padx=2)

            scorebox4 = tk.Label(frame, text=f'{scorebox[3]:>2s}', font=('DSEG7 Classic', font_size), fg=hc, bg='black')
            scorebox4.grid(row=1, column=2)

    def get_colors(self, game: Game):
        colors = ['red', 'red']
        if game.gameData.teams.away.division == 'AW':
            colors[0] = 'white'
        
        if game.gameData.teams.home.division == 'AW':
            colors[1] = 'white'

        return ['red', 'red']
        return colors

    def get_games(self):
        self.games = gm.get_games()

    def update(self):
        try:
            self.get_games()
            self.display_game_frames()
            self.window.update()
        except KeyboardInterrupt:
            sys.exit()
        finally:
            self.window.after(5000, self.update)

    def run(self):
        self.get_games()
        self.create_game_frames()
        self.display_game_frames()
        self.update()
        self.window.mainloop()

if __name__ == '__main__':
    sb = Scoreboard()
    sb.run()
