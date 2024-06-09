"""
This module finds the missed call information for a given game. This
is essentially a front for src.umpire.get_total_favored_runs. You should
only be using this module if you are running it directly. If you need
to import this module, think about importing directly from the umpire
module.

Can use --gamePk command line argument to skip input prompt
"""

import argparse
from src.umpire import Umpire
from src.plotter import Plotter


def main():
    """
    Function that gets system arguments and runs function to get
    missed call information such as number of missed calls and total
    favor. This function is essentially a front for
    src.umpire.get_total_favored_runs
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--gamePk', '--gamepk', help='gamePk', type=int)

    args = parser.parse_args()

    if args.gamePk is None:
        gamePk = int(input('gamePk: '))
    else:
        gamePk = args.gamePk

    plotter = Plotter()

    umpire = Umpire(gamepk = gamePk)
    umpire.calculate_game(method='monte')
    umpire.print_missed_calls()

    favor = umpire.home_favor
    missed_calls_list = umpire.missed_calls

    print(f'{umpire.home_favor:.2f}')
    plotter.plot(missed_calls_list)

    return favor

if __name__ == '__main__':
    main()
