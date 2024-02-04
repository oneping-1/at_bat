"""
Prints the division standings for the given league.
Uses src.standings.Standing class

leagueID:
American League: 103
National League: 104
"""

import statsapi
from src.standings import Standing

# leagueID:
# 103 - American League
# 104 - National League


if __name__ == '__main__':
    standings_data = statsapi.get('standings', {'leagueId':103})
    s = Standing(standings_data)

    for team in s.west.teamRecords:
        print(f'{team.team.abv:3s} {team.gamesBack:4.1f}')
