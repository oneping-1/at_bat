from typing import List

class Schedule:
    def __init__(self, sch: dict):
        self.totalItems = sch['totalItems']
        self.totalEvents = sch['totalEvents']
        self.totalGames = sch['totalGames']
        self.totalGamesInProgress = sch['totalGamesInProgress']
        self.dates: List[Dates] = []

        for date in sch['dates']:
            self.dates.append(Dates(date))   

class Dates:
    def __init__(self, date:dict):
        self.date = date['date']
        self.totalItems = date['totalItems']
        self.totalEvents = date['totalEvents']
        self.totalGames = date['totalGames']
        self.totalGamesInProgress = date['totalGamesInProgress']
        self.games = date['games']
        self._children()

    def _children(self):
        self.games = Games(self.games[0])

class Games:
    def __init__(self, games:dict):
        self.gamePk = games['gamePk']
        self.link = games['link']
        self.gameType = games['gameType']
        self.season = games['season']
        self.gameDate = games['gameDate']
        self.officialDate = games['officialDate']
        self.status = games['status'] # children
        self.teams = games['teams'] # children
        self.venue = games['venue'] # children
        self.content = games['content'] # children
        self.gameNumber = games['gameNumber']
        self.publicFacing = games['publicFacing']
        self.doubleHeader = games['doubleHeader']
        self.gamedayType = games['gamedayType']
        self.tiebreaker = games['tiebreaker']
        self.calendarEventID = games['calendarEventID']
        self.seasonDisplay = games['seasonDisplay']
        self.dayNight = games['dayNight']
        self.scheduledInnings = games['scheduledInnings']
        self.reverseHomeAwayStatus = games['reverseHomeAwayStatus']
        self.inningBreakLength = games['inningBreakLength']
        self.gamesInSeries = games.get('gamesInSeries', None)
        self.seriesGameNumber = games.get('seriesGameNumber', None)
        self.seriesDescription = games['seriesDescription']
        self.recordSource = games['recordSource']
        self.ifNecessary = games['ifNecessary']
        self.ifNecessaryDescription = games['ifNecessaryDescription']
        self._children()

    def _children(self):
        self.status = Status(self.status)
        self.teams = Teams(self.teams)
        self.venue = Venue(self.venue)
        self.content = Content(self.content)

class Status:
    def __init__(self, status:dict):
        self.abstractGameState = status['abstractGameState']
        self.codedGameState = status['codedGameState']
        self.detailedState = status['detailedState']
        self.statusCode = status['statusCode']
        self.startTimeTBD = status['startTimeTBD']
        self.abstractGameCode = status['abstractGameCode']
        # no children

class Teams:
    def __init__(self, teams:dict):
        self.away = teams['away']
        self.home = teams['home']
        self._children()

    def _children(self):
        self.away = Team(self.away)
        self.home = Team(self.home)

class Team:
    def __init__(self, team:dict):
        self.leagueRecord = team['leagueRecord']
        self.team = team['team']
        self.splitSquad = team['splitSquad']
        self.seriesNumber = team.get('seriesNumber', None)
        self._children()

    def _children(self):
        self.leagueRecord = LeagueRecord(self.leagueRecord)
        self.team = Team2(self.team)

class LeagueRecord:
    def __init__(self, lr:dict):
        self.wins = int(lr['wins'])
        self.losses = int(lr['losses'])
        self.pct = float(lr['pct'])
        # no children

class Team2:
    def __init__(self, team:dict):
        self.id = team['id']
        self.name = team['name']
        self.link = team['link']
        # no children

class Venue:
    def __init__(self, venue:dict):
        self.id = venue['id']
        self.name = venue['name']
        self.link = venue['link']
        # no children

class Content:
    def __init__(self, content:dict):
        self.link = content['link']
        # no children