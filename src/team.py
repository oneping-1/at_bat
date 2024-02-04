"""
Holds basic info for each team including team name, abbreviaiton,
division, and id.

Classes:
    Team: Holds basic info for each team
"""

from typing import List
import csv
import os

class Team:
    """
    Holds info for each team including id code, abbreviation, division,
    and opponent stats. Useful when you need all info at once place
    """
    def __init__(self, team_id: int, abv: str, div: str):
        self.id = int(team_id)
        self.abv = abv
        self.division = div
        self.opponent = None

    def oppo(self, wins:int, losses:int, above_500:float):
        """
        Sets the opponents info for the instance

        Args:
            wins (int): The sum of wins the opponent has over a specific
                length of time
            losses (int): The sum of losses the opponent has over a
                specific length of time
            above_500 (float): The percentage of opponents whose win/
                loss records are above .500
        """
        self.opponent = _Opponent(wins, losses, above_500)

    @classmethod
    def get_teams_list(cls) -> List['Team']:
        """
        Returns a list of Team class for all the teams.

        Returns:
            List[Team]: The list of Team class
        """
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

class _Opponent:
    """
    Holds opponent info for the Team class. Seperates info from the team
    and their opponent
    """
    def __init__(self, wins:int, losses:int, above_500:float):
        self.wins = wins
        self.losses = losses
        self.total = wins + losses
        self.win_pct = self.wins / self.total
        self.above_500 = above_500

if __name__ == '__main__':
    Team.get_teams_list()
