"""
Attempt to replicate Umpire Scorecards
Finds all missed calls from a game and prints them
along with favored runs (>0 = home favored/gained runs)
"""

from typing import List
import argparse
from tqdm import tqdm
from at_bat.statsapi_plus import get_daily_gamepks
from at_bat.game import Game
from at_bat.umpire import Umpire


def daily_ump_scorecards(date: str,
                         print_daily_stats: bool = False
                         ) -> List[Umpire]:
    """
    Finds the missed calls and favor for each game in a given day

    Gets the gamePks for all games on a given day gathers missed call
    and favored run infomation. Returns a list of class Umpire with
    missed call and favored run info. Will also print all info if
    function argument is provided

    Args:
        date (str): The date for the given days in ISO-8601 format
            (YYYY-MM-DD)
        print_daily_stats (bool, optional): Set to True to print all
            missed call info. Defaults to False

    Returns:
        games (List[Umpire]): List of games with missed calls and
            favor easily accessable as well as the full Game class

    Raises
        ConnectionError: Connection to API fails
    """
    daily_games_pk = get_daily_gamepks(date=date)
    games: List[Umpire] = []

    for game_pk in tqdm(daily_games_pk):
        game = Game.get_game_from_pk(game_pk)

        umpire = Umpire(game=game, method='monte')
        umpire.calculate_game()
        games.append(umpire)

    if print_daily_stats is True:
        for game in games:
            away_team_abv = game.game.gameData.teams.away.abbreviation
            home_team_abv = game.game.gameData.teams.home.abbreviation

            print(f'pk: {game.gamepk}')
            print(f'{away_team_abv} at {home_team_abv}')
            print(f'Misses: {game.num_missed_calls}')

            if game.home_favor < 0:
                print(f'Favor: {-game.home_favor:+5.2f} {away_team_abv}')
            else:
                print(f'Favor: {game.home_favor:+5.2f} {home_team_abv}')

            if game.home_wpa < 0:
                print(f'WPA: {-game.home_wpa*100:.1f} {away_team_abv}')
            else:
                print(f'WPA: {game.home_wpa*100:.1f} {home_team_abv}')
            print()

    return games


def main():
    """
    Main function that grabs system arguments and starts code
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=None,
                        help='date (YYYY-MM-DD)', type=str)

    parser.add_argument('--print', help='Print Missed Calls',
                        action='store_true')

    args = parser.parse_args()
    daily_ump_scorecards(print_daily_stats=True, date=args.date)


if __name__ == '__main__':
    main()
