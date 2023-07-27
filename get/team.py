from typing import List
import csv
import os

class Team:
    def __init__(self, team_id: int, abv: str, div: str):
        self.id = int(team_id)
        self.abv = abv
        self.division = div
        self.opponent = None

    def oppo(self, wins:int, losses:int, above_500:float):
        self.opponent = Opponent(wins, losses, above_500)

    @classmethod
    def get_teams_list(cls) -> List['Team']:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, '..', 'csv')
        csv_file_path = os.path.join(csv_path, 'teams.csv')

        teams = []
        with open(csv_file_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for row in reader:
                teams.append(Team(row[0], row[1], row[2]))

        return teams

class Opponent:
    def __init__(self, wins:int, losses:int, above_500:float):
        self.wins = wins
        self.losses = losses
        self.total = wins + losses
        self.win_pct = self.wins / self.total
        self.above_500 = above_500

if __name__ == '__main__':
    Team.get_teams_list()