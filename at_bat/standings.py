# pylint: disable=C0103, C0111

"""
Converts the standings_data dict returned by statsapi.get('standings')
into a class for easier data grabbing.

Classes:
    Standing: Represents the division and league standings for the
        given league (American and National)

Example:
    standings_data = statsapi.get('schedule', {'leagueId':103})
    standings_class = Standing(standings_data)
"""

import os
from typing import List, Union
import csv
import statsapi
import requests
import time

current_dir = os.path.dirname(os.path.relpath(__file__))
csv_path = os.path.join(current_dir, '..', 'csv')

class Standings:
    def __init__(self, standings):
        self.east = standings['records'][0]
        self.central = standings['records'][1]
        self.west = standings['records'][2]
        self._children()


    def _children(self):
        self.east = Records(self.east)
        self.central = Records(self.central)
        self.west = Records(self.west)

    @classmethod
    def get_dict(cls, league: str) -> dict:
        if league not in ('AL', 'NL'):
            raise ValueError('Invalid league ID. Must be AL or NL')

        if league == 'AL':
            league_id = 103
        else:
            league_id = 104

        max_retries = 10
        for i in range(max_retries):
            try:
                return statsapi.get('standings', {'leagueId': league_id, 'standingsTypes': 'springTraining'})
            except requests.exceptions.RequestException:
                print(f'RequestException ({i+1}/{max_retries})')
                # print(f'Error: {e}')
                time.sleep(min(2**i, 30))  # Exponential backoff

    @classmethod
    def get_standings(cls, league: str) -> 'Standings':
        return cls(cls.get_dict(league))

class Records:
    def __init__(self, records):
        self.standingsType = records['standingsType']
        self.league = records['league']
        self.division = records['division']
        self.sport = records['sport']
        self.lastUpdated = records['lastUpdated']

        # list of teams in division
        self.team_records = []
        self.team_records: List[TeamRecords]

        for team in records['teamRecords']:
            self.team_records.append(team)

        self._children()


    def _children(self):
        self.league = self.league['id']
        self.division = self.division['id']
        self.sport = self.sport['id']

        # list of teams in division
        self.team_records = [TeamRecords(x) for x in self.team_records]


class TeamRecords:
    def __init__(self, teamRecords):
        self.team = teamRecords['team']
        self.season = teamRecords['season']
        self.streak = teamRecords['streak']
        self.division_rank = teamRecords['divisionRank']
        self.league_rank = teamRecords['leagueRank']
        self.sport_rank = teamRecords.get('sportRank', None)
        self.games_played = int(teamRecords['gamesPlayed'])
        self.games_back = self._get_float(teamRecords['gamesBack'])
        self.wild_card_games_back = teamRecords['wildCardGamesBack']
        self.league_games_back = teamRecords['leagueGamesBack']
        self.spring_league_games_back = teamRecords['springLeagueGamesBack']
        self.sport_games_back = teamRecords['sportGamesBack']
        self.division_games_back = self._get_float(teamRecords['divisionGamesBack'])
        self.conference_games_back = teamRecords['conferenceGamesBack']
        self.last_updated = teamRecords['lastUpdated']
        self.records = teamRecords['records']
        self.runs_allowed = int(teamRecords['runsAllowed'])
        self.runs_scored = int(teamRecords['runsScored'])
        self.division_champ = bool(teamRecords.get('divisionChamp', None))
        self.division_leader = bool(teamRecords.get('divisionLeader', None))
        self.has_wildcard = bool(teamRecords.get('hasWildcard', None))
        self.clinched = bool(teamRecords.get('clinched', None))

        self.magic_number = teamRecords.get('magicNumber', None)
        self.wins = int(teamRecords['wins'])
        self.losses = int(teamRecords['losses'])
        self.run_differential = int(teamRecords['runDifferential'])
        self.winning_percentage = float(teamRecords['winningPercentage'])

        self.elimination_number = self._get_int(teamRecords.get('eliminationNumber', None))
        self.wildcard_elimination_number = self._get_int(teamRecords.get('wildCardEliminationNumber', None))

        self._children()


    def _get_int(self,string):
        if string is None:
            return None
        if string == '-':
            return 0
        if string == 'E':
            return -1
        return int(string)


    def _get_float(self,string):
        if string == '-':
            return 0
        if string == 'E':
            return -1
        return float(string)


    def _children(self):
        self.team = Team(self.team)
        self.streak = Streak(self.streak)
        self.records = Records2(self.records)


class Team:
    def __init__(self, team):
        self.id = int(team['id'])
        self.name = team['name']
        self.abv = self._abv_from_id(self.id)
        self.division = self._div_from_id(self.id)


    @classmethod
    def _abv_from_id(cls, code) -> Union[str, None]:
        file_path = os.path.join(csv_path, 'teams.csv')

        with open(file_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for team_id, abv, _ in reader:
                if code == int(team_id):
                    return abv

        return None


    @classmethod
    def _div_from_id(cls, code) -> Union[str, None]:
        file_path = os.path.join(csv_path, 'teams.csv')

        with open(file_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for team_id, _, div in reader:
                if code == int(team_id):
                    return div

        return None


class Streak:
    def __init__(self, streak):
        self.streakType = streak['streakType']
        self.streakNumber = streak['streakNumber']
        self.streakCode = streak['streakCode']


class Records2:
    def __init__(self, record):
        self.splitRecords = record['splitRecords']
        self.divisionRecrds = record['divisionRecords']
        self.leagueRecords = record['leagueRecords']
        self.expectedRecords = record['expectedRecords']
        self._children()


    def _children(self):
        self.splitRecords = SplitRecords(self.splitRecords)
        self.divisionRecrds = DivisionRecords(self.divisionRecrds)
        self.leagueRecords = LeagueRecord(self.leagueRecords)
        self.expectedRecords = ExpectedRecords(self.expectedRecords)


class SplitRecords:
    def __init__(self, splitRecords):
        self.home = SplitRecordsDetails(splitRecords[0])
        self.away = SplitRecordsDetails(splitRecords[1])
        self.left = SplitRecordsDetails(splitRecords[2])
        self.leftHome = SplitRecordsDetails(splitRecords[3])
        self.leftAway = SplitRecordsDetails(splitRecords[4])
        self.rightHome = SplitRecordsDetails(splitRecords[5])
        self.rightAway = SplitRecordsDetails(splitRecords[6])
        self.right = SplitRecordsDetails(splitRecords[7])
        self.lastTen = SplitRecordsDetails(splitRecords[8])
        self.extraInning = SplitRecordsDetails(splitRecords[9])
        self.oneRun = SplitRecordsDetails(splitRecords[10])
        self.winners = SplitRecordsDetails(splitRecords[11])
        self.day = SplitRecordsDetails(splitRecords[12])
        self.night = SplitRecordsDetails(splitRecords[13])


class SplitRecordsDetails:
    def __init__(self, srd):
        self.wins = int(srd['wins'])
        self.losses = int(srd['losses'])
        self.type = srd.get('type', None)
        self.pct = float(srd['pct'])

class DivisionRecords:
    def __init__(self, divisionRecords):
        self.west = divisionRecords[0]
        self.east = divisionRecords[1]
        self.central = divisionRecords[2]
        self._children()


    def _children(self):
        self.west = DivisionRecordsDetailed(self.west)
        self.east = DivisionRecordsDetailed(self.east)
        self.central = DivisionRecordsDetailed(self.central)


class DivisionRecordsDetailed:
    def __init__(self, drd):
        self.wins = int(drd['wins'])
        self.losses = int(drd['losses'])
        self.pct = float(drd['pct'])
        self.id = int(drd['division']['id'])
        # self.name = drd['division']['name']


class LeagueRecord:
    def __init__(self, leagueRecords):
        self.american = leagueRecords[0]
        self.national = leagueRecords[1]
        self._children()


    def _children(self):
        self.american = LeagueRecordsDetailed(self.american)
        self.national = LeagueRecordsDetailed(self.national)


class LeagueRecordsDetailed:
    def __init__(self, lrd):
        self.wins = int(lrd['wins'])
        self.losses = int(lrd['losses'])
        self.pct = float(lrd['pct'])
        self.id = int(lrd['league']['id'])
        self.name = lrd['league']['name']


class ExpectedRecords:
    def __init__(self, expectedRecords):
        self.xWinLoss = expectedRecords[0]
        self.xWinLossSeason = expectedRecords[1]
        self._children()


    def _children(self):
        self.xWinLoss = ExpectedRecordsDetailed(self.xWinLoss)
        self.xWinLossSeason = ExpectedRecordsDetailed(self.xWinLossSeason)


class ExpectedRecordsDetailed:
    def __init__(self, erd):
        self.wins = int(erd['wins'])
        self.losses = int(erd['losses'])
        self.type = erd['type']
        self.pct = float(erd['pct'])

