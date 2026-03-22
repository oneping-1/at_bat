"""
This module finds the missed call information for a given game. This
is essentially a front for src.umpire.get_total_favored_runs. You should
only be using this module if you are running it directly. If you need
to import this module, think about importing directly from the umpire
module.

Can use --gamePk command line argument to skip input prompt
"""

import argparse
import pandas as pd

from at_bat.game_parser import GameParser
from at_bat.plotter import Plotter


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

    # if args.gamePk is None:
    #     gamePk = int(input('gamePk: '))
    # else:
    #     gamePk = args.gamePk

    gamePk = 831553

    parser = GameParser(gamepk=gamePk)

    df = parser.dataframe.loc[
        (parser.dataframe['umpire_wp_favor'] != 0) |
        (parser.dataframe['umpire_run_favor'] != 0)
    ].reset_index(drop=True)

    for i, row in df.iterrows():
        half_inning = 'Bottom' if row['is_top_inning'] is False else 'Top'
        runners = f'{3*row["is_third_base"]}{2*row["is_second_base"]}{1*row["is_first_base"]}'

        balls = row['balls']
        strikes = row['strikes']

        print(f'{i}: {half_inning} {row["inning"]}')
        print(f'{row["pitcher"]} to {row["batter"]}')
        print(f'{runners}, {row["outs"]} outs {balls}-{strikes}')
        print(f'px: {row["px"]:.3f} | pz: {row["pz"]:.3f}')
        print(f'px_min: {row["px_min"]:.3f} | px_max: {row["px_max"]:.3f}')
        print(f'pz_min: {row["pz_min"]:.3f} | pz_max: {row["pz_max"]:.3f}')
        print(f'Runs: {row["umpire_run_favor"]:.2f} | WP: {row["umpire_wp_favor"]*100:.1f}%')

        print()

    print(f'Total Run Favor: {df["umpire_run_favor"].sum():.3f}')
    print(f'Total WP Favor: {df["umpire_wp_favor"].sum():.3f}')

    Plotter(df, show=True)

    return (float(df['umpire_wp_favor'].sum()), float(df['umpire_run_favor'].sum()))

if __name__ == '__main__':
    main()
