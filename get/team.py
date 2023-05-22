from typing import List
import csv

class Team:
    def __init__(self, id, abv, div):
        self.id = int(id)
        self.abv = abv
        self.division = div

    def oppo(self, wins:int, losses:int, above_500:float):
        self.opponent = Opponent(wins, losses, above_500)

class Opponent:
    def __init__(self, wins:int, losses:int, above_500:float):
        self.wins = wins
        self.losses = losses
        self.total = wins + losses
        self.win_pct = self.wins / self.total
        self.above_500 = above_500

def get_teams_list() -> List[Team]:
    teams = []

    with open('teams.csv') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            teams.append(Team(row[0], row[1], row[2]))

    return teams