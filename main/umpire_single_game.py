"""
This module finds the missed call information for a given game. This
is essentially a front for get.umpire.get_total_favored_runs. You should
only be using this module if you are running it directly. If you need
to import this module, think about importing directly from the umpire
module.

Can use --gamePk command line argument to skip input prompt
"""

import argparse
from get.umpire import Umpire
from get.plotter import Plotter


def main():
    """
    Function that gets system arguments and runs function to get
    missed call information such as number of missed calls and total
    favor. This function is essentially a front for
    get.umpire.get_total_favored_runs
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--gamePk', '--gamepk', help='gamePk', type=int)

    args = parser.parse_args()

    if args.gamePk is None:
        gamePk = int(input('gamePk: '))
    else:
        gamePk = args.gamePk

    plotter = Plotter()

    method = Umpire.delta_favor_zone
    results = Umpire.find_missed_calls(gamePk=gamePk, print_missed_calls=True,
                                       delta_favor_func=method)
    _, favor, missed_list = results

    print(f'{favor:.2f}')
    plotter.plot(missed_list)

    return favor


if __name__ == '__main__':
    print(f'{main():.2f}')
