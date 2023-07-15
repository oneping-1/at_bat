from datetime import datetime
from datetime import timedelta
import sys
import statsapi
from colorama import just_fix_windows_console
from tqdm import tqdm
from get.statsapi_plus import get_color
from get.team import get_teams_list
from get.schedule import Schedule

just_fix_windows_console()

def sos(days_ahead=15):
    today = datetime.now()
    ahead = today + timedelta(days=days_ahead)

    today = f'{today.year:4d}-{today.month:02d}-{today.day:02d}'
    ahead = f'{ahead.year:4d}-{ahead.month:02d}-{ahead.day:02d}'

    teams = get_teams_list()

    for team in tqdm(teams):
        data = statsapi.get('schedule',
                            {'sportId':1, 'startDate':today, 'endDate':ahead, 'teamId':team.id})

        data = Schedule(data)

        wins = 0
        losses = 0
        above_500 = 0

        for day in data.dates:
            if team.id != day.games.teams.away.team.id and team.id != day.games.teams.home.team.id:
                sys.exit('id mismatch')
            elif team.id != day.games.teams.away.team.id:
                wins += day.games.teams.away.leagueRecord.wins
                losses += day.games.teams.away.leagueRecord.losses
                if day.games.teams.away.leagueRecord.pct > .500:
                    above_500 += 1
            elif team.id != day.games.teams.home.team.id:
                wins += day.games.teams.home.leagueRecord.wins
                losses += day.games.teams.home.leagueRecord.losses
                if day.games.teams.home.leagueRecord.pct > .500:
                    above_500 += 1
            else:
                sys.exit('id mismatch 2')

        team.oppo(wins, losses, above_500)

    print(f'\nDays = {days_ahead}')
    print(' # | team |  win% | >500')
    for i, team in enumerate(sorted(teams, key=lambda x: x.opponent.win_pct, reverse=True)):
        print(f'{get_color(team.abv, team.division)}{i+1:2d} | ', end='')
        print(f'{team.abv:4s} | ', end='')
        print(f'{team.opponent.win_pct:.3f} | ', end='')
        print(f'{team.opponent.above_500:2d}')


if __name__ == '__main__':
    sos(days_ahead=14)
