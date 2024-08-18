"""
Prints the division standings for the given league.
Uses src.standings.Standing class

leagueID:
American League: 103
National League: 104
"""

import statsapi
from src.standings import Standing
import json

# leagueID:
# 103 - American League
# 104 - National League


if __name__ == '__main__':
    standings_data = statsapi.get('standings', {'leagueId':103}
    s = Standing(standings_data)

    for team in s.west.teamRecords:
        s = f'{team.team.abv:3s}'
        s += f' | {team.gamesBack:4.1f}'
        s += f' | {team.eliminationNumber:2d}'
        s += f' | {team.wildCardEliminationNumber:2d}'
        print(s)
