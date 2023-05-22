from typing import List
from .team_lookup import div_from_id, abv_from_id
from colorama import Fore, just_fix_windows_console

class Standing:
    def __init__(self, standings):
        self.east = standings['records'][0]
        self.central = standings['records'][1]
        self.west = standings['records'][2]
        self._children()

    def _children(self):
        self.east = Records(self.east)
        self.central = Records(self.central)
        self.west = Records(self.west)

class Records:
    def __init__(self, records):
        self.standingsType = records['standingsType']
        self.league = records['league']
        self.division = records['division']
        self.sport = records['sport']
        self.lastUpdated = records['lastUpdated']

        # list of teams in division
        self.teamRecords = []
        self.teamRecords: List[TeamRecords]

        for team in records['teamRecords']:
            self.teamRecords.append(team)

        self._children()

    def _children(self):
        self.league = self.league['id']
        self.division = self.division['id']
        self.sport = self.sport['id']

        # list of teams in division
        self.teamRecords = [TeamRecords(x) for x in self.teamRecords]

class TeamRecords:
    def __init__(self, teamRecords):
        self.team = teamRecords['team']
        self.season = teamRecords['season']
        self.streak = teamRecords['streak']
        self.divisionRank = teamRecords['divisionRank']
        self.leagueRank = teamRecords['leagueRank']
        self.sportRank = teamRecords['sportRank']
        self.gamesPlayed = int(teamRecords['gamesPlayed'])
        self.gamesBack = self._get_float(teamRecords['gamesBack'])
        self.wildCardGamesBack = teamRecords['wildCardGamesBack']
        self.leagueGamesBack = teamRecords['leagueGamesBack']
        self.springLeagueGamesBack = teamRecords['springLeagueGamesBack']
        self.sportGamesBack = teamRecords['sportGamesBack']
        self.divisionGamesBack = teamRecords['divisionGamesBack']
        self.conferenceGamesBack = teamRecords['conferenceGamesBack']
        self.lastUpdated = teamRecords['lastUpdated']
        self.records = teamRecords['records']
        self.runsAllowed = int(teamRecords['runsAllowed'])
        self.runsScored = int(teamRecords['runsScored'])
        self.divisionChamp = bool(teamRecords['divisionChamp'])
        self.divisionLeader = bool(teamRecords['divisionLeader'])
        self.hasWildcard = bool(teamRecords['hasWildcard'])
        self.clinched = bool(teamRecords['clinched'])

        self.eliminationNumber = self._get_int(teamRecords['eliminationNumber'])
        self.wildCardEliminationNumber = self._get_int(teamRecords['wildCardEliminationNumber'])
        self.magicNumber = teamRecords.get('magicNumber', None)
        self.wins = int(teamRecords['wins'])
        self.losses = int(teamRecords['losses'])
        self.runDifferential = int(teamRecords['runDifferential'])
        self.winningPercentage = float(teamRecords['winningPercentage'])
        self._children()
    
    def _get_int(self,string):
        if string == '-':
            return 0
        else:
            return int(string)
        
    def _get_float(self,string):
        if string == '-':
            return 0
        else:
            return float(string)

    def _children(self):
        self.team = Team(self.team)
        self.streak = Streak(self.streak)
        self.records = Records2(self.records)
        
class Team:
    def __init__(self, team):
        self.id = int(team['id'])
        self.name = team['name']
        self.abv = abv_from_id(self.id)
        self.division = div_from_id(self.id)

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
        self.leagueRecords = LeagueRecords(self.leagueRecords)
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
        self.type = srd['type']
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
        self.name = drd['division']['name']

class LeagueRecords:
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

def get_color(team:Team):
    if team.abv == 'TEX':
        return Fore.LIGHTBLUE_EX
    elif team.division == 'AW':
        return Fore.LIGHTRED_EX
    else:
        return Fore.WHITE
