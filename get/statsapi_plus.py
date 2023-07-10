import statsapi
from colorama import Fore
from typing import List
from .team import Team

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

if __name__ == '__main__':
    pass

