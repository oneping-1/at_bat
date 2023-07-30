"""
Module that prints live MLB scores for a given day in a format similar
to a out-of-town scoreboard. Has team abbreviations, score, outs,
runners, and inning. Also will print if a game is final or in a delay.

You can change the colors of each team in the get_color_scoreboard
function in the statsapi_plus.py module

This module takes in one command line prompt '--delay' which is the
number of seconds you want the scoreboard to be delayed. Useful to not
get spoiled of scores before they happen on devices
"""

import argparse
from get.games import Games


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', help='Delay in seconds', type=int)
    args = parser.parse_args()

    if args.delay is None:
        args.delay = 0

    scoreboard = Games(args.delay)
    scoreboard.scoreboard()


if __name__ == '__main__':
    main()