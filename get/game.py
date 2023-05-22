import datetime
import pytz
from typing import List
from .statsapi_plus import get_gamePks
from tqdm import tqdm
import statsapi

class Game:
    def __init__(self, data:dict):
        self.gameData = data['gameData']
        self.liveData = data['liveData']
        self._children()

    def _children(self):
        self.gameData = GameData(self.gameData)
        self.liveData = LiveData(self.liveData)

class GameData:
    def __init__(self, gameData):
        self.game = gameData['game']
        self.datetime = gameData['datetime']
        self.status = gameData['status']
        self.teams = gameData['teams']
        self.players = gameData['players']
        self.weather = gameData['weather']
        self.flags = gameData['flags']
        self.probablePitchers = gameData['probablePitchers']
        self._children()

    def _children(self):
        self.datetime = Datetime(self.datetime)
        self.status = Status(self.status)
        self.teams = TeamsGameData(self.teams)
        #self.weather = Weather(self.weather)
        self.flags = Flags(self.flags)

class Datetime:
    def __init__(self, datetime):
        self.dateTime = datetime['dateTime']
        self.officialDate = datetime['officialDate']
        self.startHour, self.startMin = _convert_zulu_to_local(self.dateTime)
        self.startTime = f'{self.startHour} {self.startMin}'
        # no children

class Status:
    def __init__(self, status):
        self.abstractGameState = status['abstractGameState']
        self.detailedState = status['detailedState']
        # no children

class TeamsGameData:
    def __init__(self, teams):
        self.away = teams['away']
        self.home = teams['home']
        self._children()

    def _children(self):
        self.away = TeamGameData(self.away)
        self.home = TeamGameData(self.home)

class TeamGameData:
    def __init__(self, team):
        self.id = team['id']
        self.abbreviation = team['abbreviation']
        self.teamName = team['teamName']
        self.division = _get_division(self.id)
        # no children

class Weather:
    def __init__(self, weather):
        self.condition = weather.get('condition', None)
        self.temp = weather['temp']
        self.wind = weather['wind']
        # no children

class Flags:
    def __init__(self, flags):
        self.noHitter = flags['noHitter']
        self.perfectGame = flags['perfectGame']
        # no children

class LiveData:
    def __init__(self, liveData):
        self.plays = liveData['plays']
        self.linescore = liveData['linescore']
        self.boxscore = liveData['boxscore']
        self.decisions = liveData.get('decision', {})
        self._children()

    def _children(self):
        self.plays = Plays(self.plays)
        self.linescore = Linescore(self.linescore)

class Plays:
    def __init__(self, plays):
        self.currentPlay = plays.get('currentPlay', None)
        # children but dont care

class Linescore:
    def __init__(self, linescore):
        self.currentInning = linescore.get('currentInning', None)
        self.currentInningOrdinal = linescore.get('currentInningOrdinal', None)
        self.inningState = linescore.get('inningState', None)
        self.teams = linescore['teams']
        self.defense = linescore['defense']
        self.offense = linescore['offense']
        self.balls = linescore.get('balls', None)
        self.strikes = linescore.get('strikes', None)
        self.outs = linescore.get('outs', None)

        self._children()

    def _children(self):
        self.teams = TeamsLinescore(self.teams)
        self.offense = Offense(self.offense)

class TeamsLinescore:
    def __init__(self, teams):
        self.home = teams['home']
        self.away = teams['away']
        self._children()

    def _children(self):
        self.home = TeamLinescore(self.home)
        self.away = TeamLinescore(self.away)

class TeamLinescore:
    def __init__(self, team):
        self.runs = team.get('runs', None)
        self.hits = team.get('hits', None)
        self.errors = team.get('errors', None)
        # no children

class Offense:
    def __init__(self, offense):
        self.batter = offense.get('batter', None)
        self.onDeck = offense.get('onDeck', None)
        self.inHole = offense.get('inHole', None)
        self.first = offense.get('first', None)
        self.second = offense.get('second', None)
        self.third = offense.get('third', None)
        self.pitcher = offense.get('pitcher', None)
        self._children()

        self.runners = (1 if self.first else 0) + (2 if self.second else 0) + (4 if self.third else 0)
        self.is_first = self.first is not None
        self.is_second = self.second is not None
        self.is_third = self.third is not None

    def _children(self):
        if self.batter:
            self.batter = Player(self.batter)

        if self.onDeck:
            self.onDeck = Player(self.onDeck)

        if self.inHole:
            self.inHole = Player(self.inHole)

        if self.first:
            self.first = Player(self.first)

        if self.second:
            self.second = Player(self.second)
        
        if self.third:
            self.third = Player(self.third)
        
        if self.pitcher:
            self.pitcher = Player(self.pitcher)

class Player:
    def __init__(self, player):
        self.id = player['id']
        self.fullName = player['fullName']
        # no children

class Decisions:
    def __init__(self, decision):
        self.winner = decision['winner']
        self.loser = decision['loser']
        self._children()

    def _children(self):
        self.winner = Player(self.winner)
        self.loser = Player(self.loser)

def _convert_zulu_to_local(zulu_time_str):
    zulu_time = datetime.datetime.strptime(zulu_time_str, '%Y-%m-%dT%H:%M:%SZ')
    zulu_time = pytz.utc.localize(zulu_time)

    local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    local_time = zulu_time.astimezone(local_timezone)

    t = local_time.strftime('%I:%M')

    if t[0] == str('0'):
        t = f' {t[1:]}'

    t = f'{t[0:2]} {t[3:]}'

    return [t[0:2], t[3:]]

def _get_division(code:int):
    match code:
        case 108: # LAA
            return 'AW'
        case 109: # ARI
            return 'NW'
        case 110: # BAL
            return 'AE'
        case 111: # BOS
            return 'AE'
        case 112: # CHC
            return 'NC'
        case 113: # CIN
            return 'NC'
        case 114: # CLE
            return 'AC'
        case 115: # COL
            return 'NW'
        case 116: # DET
            return 'AC'
        case 117: # HOU
            return 'AW'
        case 118: # KC
            return 'AC'
        case 119: # LAD
            return 'NW'
        case 120: # WSH
            return 'NE'
        case 121: # NYM
            return 'NE'
        case 133: # OAK
            return 'AW'
        case 134: # PIT
            return 'NC'
        case 135: # SD
            return 'NW'
        case 136: # SEA
            return 'AW'
        case 137: # SF
            return 'NW'
        case 138: # STL
            return 'NC'
        case 139: # TB
            return 'AE'
        case 140: # TEX
            return 'AW'
        case 141: # TOR
            return 'AE'
        case 142: # MIN
            return 'AC'
        case 143: # PHI
            return 'NE'
        case 144: # ATL
            return 'NE'
        case 145: # CWS
            return 'AC'
        case 146: # MIA
            return 'NE'
        case 147: # NYY
            return 'AE'
        case 158: # MIL
            return 'NC'
        
def get_games() -> List[Game]:
    gamePks = get_gamePks()
    games = []

    for Pk in tqdm(gamePks):
        data = statsapi.get('game', {'gamePk': Pk})
        games.append(Game(data))

    return games