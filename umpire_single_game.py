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
    parser.add_argument('--gamePk', default=None,
                        help='gamePk', type=int)

    args = parser.parse_args()

    if args.gamePk is None:
        args.gamePk = int(input('gamePk: '))

    plotter = Plotter()

    _, favor, missed_list = Umpire.find_missed_calls(gamePk=args.gamePk,
                                           print_missed_calls=True)

    print(f'{favor:.2f}')
    plotter.plot(missed_list)

    return favor


if __name__ == '__main__':
    print(f'{main():.2f}')
