import statsapi
from colorama import just_fix_windows_console
from get.standings import Standing, get_color

# leagueID:
# 103 - American League
# 104 - National League

just_fix_windows_console()

standings_data = statsapi.get('standings', {'leagueId':103})
s = Standing(standings_data)

for team in s.west.teamRecords:
    color = get_color(team.team)
    print(f'{color}{team.team.abv:3s} {team.gamesBack:4.1f}')