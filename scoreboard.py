import sys
from colorama import just_fix_windows_console
from get.game import Game
import get.statsapi_plus as sp
import argparse

just_fix_windows_console()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delay', help='delay in seconds', type=float, default=0)
    args = parser.parse_args()

    prnt = ''

    gamePks = sp.get_daily_gamePks()
    games = []
    for game in gamePks:
        prnt_bool = True
        data = sp.get_game_dict(game, delay_seconds=args.delay)
        game = Game(data)
        games.append(game)

        away_color, home_color = sp.get_color_scoreboard(game)

        if 'Final' in game.gameData.status.abstractGameState:
            if game.liveData.linescore.currentInning == 9:
                prnt += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  F\n')
                prnt += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d}\n')
            else:
                prnt += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  F\n')
                prnt += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Delay' in game.gameData.status.detailedState:
            prnt += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  D\n')
            prnt += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Suspended' in game.gameData.status.detailedState:
            prnt += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d}  S\n')
            prnt += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Preview' in game.gameData.status.abstractGameState or 'Warmup' in game.gameData.status.detailedState:
            prnt += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.gameData.datetime.startTime}\n')
            prnt += (f'{home_color}{game.gameData.teams.home.abbreviation:4s}\n')
        elif 'Top' in game.liveData.linescore.inningState or 'Mid' in game.liveData.linescore.inningState:
            prnt += (f'{away_color}{game.gameData.teams.away.abbreviation:3s}- {game.liveData.linescore.teams.away.runs:2d} o{game.liveData.linescore.outs:1d}\n')
            prnt += (f'{home_color}{game.gameData.teams.home.abbreviation:4s} {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')
        elif 'Bot' in game.liveData.linescore.inningState or 'End' in game.liveData.linescore.inningState:
            prnt += (f'{away_color}{game.gameData.teams.away.abbreviation:4s} {game.liveData.linescore.teams.away.runs:2d} o{game.liveData.linescore.outs:1d}\n')
            prnt += (f'{home_color}{game.gameData.teams.home.abbreviation:3s}- {game.liveData.linescore.teams.home.runs:2d} {game.liveData.linescore.currentInning:2d}\n')

        if prnt_bool:
            prnt += '\n'

    print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
    print(prnt)


if __name__ == '__main__':
    while True:
        try:
            main()
        except KeyboardInterrupt:
            sys.exit('Exited')
