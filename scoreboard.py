import statsapi
from get.game import Game
import json
from colorama import just_fix_windows_console
import sys
import get.statsapi_plus as sp

just_fix_windows_console

def main():
    s = ''

    gamePks = sp.get_gamePks()
    games = []
    for Pk in gamePks:
        p = True
        data = statsapi.get('game', {'gamePk': Pk})
        game = Game(data)
        games.append(game)

        away_color, home_color = sp.get_color_scoreboard(game)

        #s += f'{Fore.WHITE}{Pk} | {game.gameData.status.abstractGameState} | {game.gameData.status.detailedState}\n'

        if 'Final' in game.gameData.status.abstractGameState:
           if game.liveData.linescore.currentInning == 9:
                s += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  F\n')
                s += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d}\n')
           else:
                s += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  F\n')
                s += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Delay' in game.gameData.status.detailedState:
           s += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  D\n')
           s += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Suspended' in game.gameData.status.detailedState:
           s += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  S\n')
           s += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Preview' in game.gameData.status.abstractGameState or 'Warmup' in game.gameData.status.detailedState:
           s += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.gameData.datetime.startTime}\n')
           s += (f'{home_color}{game.gameData.teams.home.abbreviation:4s}\n')
        elif 'TEX' in game.gameData.teams.away.abbreviation or 'TEX' in game.gameData.teams.home.abbreviation:
            p = False
        elif 'Top' in game.liveData.linescore.inningState or 'Mid' in game.liveData.linescore.inningState:   
           s += (f'{away_color}{game.gameData.teams.away.abbreviation:3s}- {game.liveData.linescore.teams.away.runs:2d} o{game.liveData.linescore.outs:1d}\n')
           s += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Bot' in game.liveData.linescore.inningState or 'End' in game.liveData.linescore.inningState:
           s += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d} o{game.liveData.linescore.outs:1d}\n')
           s += (f'{home_color}{game.gameData.teams.home.abbreviation:3s}- {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')

        if p:
            s += '\n'

    print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
    print(s)

if __name__ == '__main__':
    while True:
        try:
            main()
        except KeyboardInterrupt:
            sys.exit('Exited')
        except:
            pass