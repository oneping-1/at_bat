import statsapi
from colorama import Fore
from typing import List
from .team import Team
import numpy as np
import csv

def get_daily_gamePks():
    gamePks = []
    data = statsapi.schedule()
    
    for game in data:
        gamePks.append(game['game_id'])

    return gamePks

def get_color_scoreboard(game):
    away = Fore.WHITE
    home = Fore.WHITE

    if 'Final' in game.gameData.status.abstractGameState or 'Preview' in game.gameData.status.abstractGameState or 'Warmup' in game.gameData.status.detailedState or 'Suspended' in game.gameData.status.detailedState:
        away = Fore.LIGHTBLACK_EX
        home = Fore.LIGHTBLACK_EX

    if game.gameData.teams.away.division == 'AW':
        away = Fore.LIGHTRED_EX
    
    if game.gameData.teams.home.division == 'AW':
        home = Fore.LIGHTRED_EX

    if game.gameData.teams.away.abbreviation == 'TEX':
        away = Fore.LIGHTBLUE_EX

    if game.gameData.teams.home.abbreviation == 'TEX':
        home = Fore.LIGHTBLUE_EX

    return [away, home]

def get_color(team_abv:str, division:str):
    if team_abv == 'TEX':
        return Fore.LIGHTBLUE_EX
    elif division == 'AW':
        return Fore.LIGHTRED_EX
    else:
        return Fore.WHITE

def get_run_expectency_numpy() -> np.ndarray:
    renp = np.zeros((5,4,4,8))

    with open('csv/re.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            b = int(row[0])
            s = int(row[1])
            o = int(row[2])
            r = int(row[3])
            re = float(row[4])

            renp[b][s][o][r] = re

    return renp

if __name__ == '__main__':
    pass

