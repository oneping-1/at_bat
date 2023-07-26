"""
Prints the average win percentage and number of opponents who have a 
winning record for a given number of days ahead.
"""

import argparse
from datetime import datetime
from datetime import timedelta
from typing import List
import statsapi
from colorama import just_fix_windows_console
from tqdm import tqdm
from get.statsapi_plus import get_color
from get.team import Team
from get.schedule import Schedule

just_fix_windows_console()


def sos(days_ahead=15, print_results = False):
    """
    Prints average win percentage and number of opponents with a winning
    record for a given time period.

    Args:
        days_ahead (int, optional): The number of days ahead you want to
            look on a teams schedule. Defaults to 15
        print_results (bool, optional): Determines if the results are
            printed or not. Defaults to False

    Returns:
        teams (List[get.team.Team]): List of teams using the Team class.
            The team class has a opponent instance variable with much
            of the relevant info this function returns

    Raises:
        TypeError: If days_ahead argument is not type int
        HTTPError: If internet connection is lost
    """
    if isinstance(days_ahead, int) is False:
        raise TypeError('days_ahead argument must be type int')

    today = datetime.now()
    ahead = today + timedelta(days=days_ahead)

    today = f'{today.year:4d}-{today.month:02d}-{today.day:02d}'
    ahead = f'{ahead.year:4d}-{ahead.month:02d}-{ahead.day:02d}'

    teams: List[Team] = Team.get_teams_list()

    for team in tqdm(teams):
        data = statsapi.get('schedule',
                            {'sportId':1, 'startDate':today,
                             'endDate':ahead, 'teamId':team.id})

        data = Schedule(data)

        wins = 0
        losses = 0
        above_500 = 0

        for day in data.dates:
            away_id = day.games.teams.away.team.id
            home_id = day.games.teams.home.team.id

            if team.id not in (away_id, home_id):
                raise ValueError('id mismatch')
            if team.id == away_id and team.id == home_id:
                raise ValueError('id mismatch')

            if team.id != away_id:
                wins += day.games.teams.away.leagueRecord.wins
                losses += day.games.teams.away.leagueRecord.losses
                if day.games.teams.away.leagueRecord.pct > .500:
                    above_500 += 1
            elif team.id != home_id:
                wins += day.games.teams.home.leagueRecord.wins
                losses += day.games.teams.home.leagueRecord.losses
                if day.games.teams.home.leagueRecord.pct > .500:
                    above_500 += 1

        team.oppo(wins, losses, above_500)

    if print_results is True:
        _print_winpct_above500(days_ahead, teams)

    return teams


def _print_winpct_above500(days_ahead:int, teams: List[Team]):
    print(f'\nDays = {days_ahead}')
    print(' # | team |  win% | >500')

    sorted_teams = sorted(teams, key=lambda x: x.opponent.win_pct, reverse=True)
    for i, team in enumerate(sorted_teams):
        print(f'{get_color(team.abv, team.division)}{i+1:2d} | ', end='')
        print(f'{team.abv:4s} | ', end='')
        print(f'{team.opponent.win_pct:.3f} | ', end='')
        print(f'{team.opponent.above_500:2d}')


def main():
    """
    Gets system arguments and parses them before running sos() function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--days', '--days_ahead',
                        help = 'Number of days ahead',
                        type = int)
    
    args = parser.parse_args()

    if args.days is None:
        args.days = 15

    sos(days_ahead=args.days, print_results = True)

if __name__ == '__main__':
    main()