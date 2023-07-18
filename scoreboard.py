import curses
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

        game_data = _get_gameData(game)
        away_color, home_color, away_team, home_team, detailed_state, abstract_state = game_data

        live_data = _get_liveData(game)
        away_score, home_score, inning, outs, isTopInning, inning_state = live_data

        if 'Final' in abstract_state:
            if game.inning == 9:
                prnt += (f'{away_color}{away_team:4s} {away_score:2d}  F\n')
                prnt += (f'{home_color}{home_team:4s} {home_score:2d}\n')
            else:
                prnt += (f'{away_color}{away_team:4s} {away_score:2d}  F\n')
                prnt += (f'{home_color}{home_team:4s} {home_score:2d} {inning:2d}\n')
        elif 'Delay' in detailed_state:
            prnt += (f'{away_color}{away_team:4s} {away_score:2d}  D\n')
            prnt += (f'{home_color}{home_team:4s} {home_score:2d} {inning:2d}\n')
        elif 'Suspended' in detailed_state:
            prnt += (f'{away_color}{away_team:4s} {away_score:2d}  S\n')
            prnt += (f'{home_color}{home_team:4s} {home_score:2d} {inning:2d}\n')
        elif 'Preview' in abstract_state or 'Warmup' in detailed_state:
            prnt += (f'{away_color}{away_team:4s} {game.gameData.datetime.startTime}\n')
            prnt += (f'{home_color}{home_team:4s}\n')
        elif inning_state in ('Top', 'Mid'):
            prnt += (f'{away_color}{away_team:3s}- {away_score}:2d o{outs:1d}\n')
            prnt += (f'{home_color}{home_team:4s} {home_score:2d} {inning:2d}\n')
        elif inning_state in ('Bot', 'End'):
            prnt += (f'{away_color}{away_team:4s} {away_score:2d} o{outs:1d}\n')
            prnt += (f'{home_color}{home_team:3s}- {home_score:2d} {inning:2d}\n')

        if prnt_bool:
            prnt += '\n'

    print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
    print(prnt)


def _get_gameData(game):
    # need to update get_colors for curses
    # this color code is placeholder
    away_color, home_color = sp.get_color_scoreboard(game)
    away_team = game.gameData.teams.away.abbreviation
    home_team = game.gameData.teams.home.abbreviation

    detailed_state = game.gameData.status.detailedState
    abstract_state = game.gameData.status.abstractGameState

    return(away_color, home_color, away_team, home_team, detailed_state, abstract_state)


def _get_liveData(game):
    away_score = game.liveData.linescore.teams.away.runs
    home_score = game.liveData.linescore.teams.home.runs

    inning = game.liveData.linescore.currentInning
    outs = game.liveData.linescore.outs

    # What is this in middle and end of innings?
    isTopInning = game.liveData.linescore.isTopInning
    inning_state = game.liveData.linescore.inningState

    return (away_score, home_score, inning, outs, isTopInning, inning_state)


if __name__ == '__main__':
    main()
