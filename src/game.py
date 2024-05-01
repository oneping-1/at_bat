"""
Converts the Python dictionary returned by statsapi.get('game') into
classes that represent each level in the dictionary returned by
statsapi.get('game').

Important classes are:
    Game: Represents the entire game
    AllPlays: A class that is typically stored in a list that represents
        each at bat in a game
    PlayEvents: A class that is again typically stored in a list that
        represents each pitch in an at bat. Also has data for pickoffs,
        mound visits, pitching changes, and pinch players

Example
from src.statsapi_plus import get_game_dict
from src.game import Game

game_dict = get_game_dict(gamePk)
game_class = Game(game_dict)
"""
# pylint: disable=C0103, C0111

import os
import datetime
from typing import List, Tuple
import math
import pytz
import statsapi
from tqdm import tqdm
from src.statsapi_plus import get_daily_gamepks
from src.statsapi_plus import get_run_expectency_difference_numpy
from src.statsapi_plus import get_game_dict

MARGIN_OF_ERROR = 0.25/12 # Margin of Error of hawkeye system (inches)

# Update for new game states for custom game_state attribute
KNOWN_GAMESTATES = ('S','P','PI','PR','PY','PW','I','IO','IR','MA','MC',
                    'ME','MF','MG','MH','MI','MO','MP','MS','MT','MU',
                    'MV','MQ','MY','NF','NJ','NN','NH','TR','UR','O',
                    'OR','F','FG','FR','DI','DC','DR')

class Game:
    """
    Initial class that the user interacts with to get the class started.
    The argument for this class is the dictionary returned by
    either statsapi.get() or get_game_dict() (both return the same
    thing).
    """
    def __init__(self, data:dict):
        self.gameData = data['gameData']
        self.liveData = data['liveData']
        self.gamepk = data.get('gamePk', None)
        self._game_dict = data
        self._children()

        if self.gameData.status.statusCode not in KNOWN_GAMESTATES:
            self._unknown_statuscode()

    def _children(self):
        self.gameData = GameData(self.gameData)
        self.liveData = LiveData(self.liveData)

    def _unknown_statuscode(self):
        abstractGameState = self.gameData.status.abstractGameState
        abstractGameCode = self.gameData.status.abstractGameCode
        detailedState = self.gameData.status.detailedState
        codedGameState = self.gameData.status.codedGameState
        statusCode = self.gameData.status.statusCode

        current_dir = os.path.dirname(os.path.relpath(__file__))
        csv_folder = os.path.join(current_dir, '..', 'csv')
        path = os.path.join(csv_folder, 'unknown_statusCodes.txt')

        now = datetime.datetime.now()
        time = now.isoformat()

        with open(path, 'a', encoding='utf-8') as file:
            file.write(f'gamepk: {self.gamepk}\n')

            file.write(f'inning: {self.liveData.linescore.currentInning}\n')
            file.write(f'inningState: {self.liveData.linescore.inningState}\n')
            file.write(f'outs: {self.liveData.linescore.outs}\n')
            file.write(f'time: {time}\n')
            file.write(f'astractGameState: {abstractGameState}\n')
            file.write(f'abstractGameCode: {abstractGameCode}\n')
            file.write(f'detailedState: {detailedState}\n')
            file.write(f'codedGameState: {codedGameState}\n')
            file.write(f'statusCode: {statusCode}\n')
            file.write('\n')

        print(f'gamepk: {self.gamepk}')
        print(f'time: {time}')
        print(f'astractGameState: {abstractGameState}')
        print(f'abstractGameCode: {abstractGameCode}')
        print(f'detailedState: {detailedState}')
        print(f'codedGameState: {codedGameState}')
        print(f'statusCode: {statusCode}')
        print('\n')

    def __repr__(self):
        return f'{self.gamepk}'

    def __eq__(self, other):
        if self._game_dict == other._game_dict:
            return True
        return False

    @classmethod
    def get_game_from_pk(cls, gamepk: int, delay_seconds: int = 0) -> 'Game':
        """
        Returns a game instance for the given game based of the gamePk

        Args:
            gamepk (int): gamepk of the game
            delay_seconds (int): Delay in seconds

        Returns:
            Game: Game class instance
        """
        if gamepk is None:
            raise ValueError('gamePk not provided')

        game_dict = get_game_dict(gamepk=gamepk, delay_seconds=delay_seconds)
        return Game(game_dict)


class GameData:
    """
    doc string
    """
    def __init__(self, gameData):
        # comment
        self._gameData = gameData
        self.game = gameData['game']
        self.datetime = gameData['datetime']
        self.status = gameData['status']
        self.teams = gameData['teams']
        self.players = gameData['players']
        self.weather = gameData.get('weather', None)
        self.gameInfo = gameData['gameInfo']
        self.flags = gameData['flags']
        self.probablePitchers = gameData['probablePitchers']
        self.officialScorer = gameData.get('officialScorer', None)
        self.primaryDatacaster = gameData.get('primaryDatacaster', None)
        self._children()

    def _children(self):
        self.datetime = Datetime(self.datetime)
        self.status = Status(self.status)
        self.teams = TeamsGameData(self.teams)
        self.weather = Weather(self.weather)
        self.gameInfo = GameInfo(self.gameInfo)
        self.flags = Flags(self.flags)

        if self.officialScorer:
            self.officialScorer = OfficialScorer(self.officialScorer)

        if self.primaryDatacaster:
            self.primaryDatacaster = PrimaryDatacaster(self.primaryDatacaster)

    def __repr__(self):
        date = self.datetime.officialDate
        away_team = self.teams.away.abbreviation
        home_team = self.teams.home.abbreviation

        return f'{date}: {away_team} at {home_team}'

    def __eq__(self, other):
        if self._gameData == other._gameData:
            return True
        return False


class Datetime:
    def __init__(self, times):
        self.dateTime = times.get('dateTime', None)
        self.officialDate = times['officialDate']

        self.startHour: int
        self.startMinute: int

        start_time = _convert_zulu_to_local(self.dateTime)
        self.startHour, self.startMinute = start_time

        self.startTime = f'{self.startHour}:{self.startMinute:02d}'
        self.startTime_sb = f'{self.startHour:2d} {self.startMinute:02d}'
        # no children


class Status:
    def __init__(self, status):

        self.abstractGameState = status['abstractGameState']
        self.detailedState = status['detailedState']
        self.codedGameState = status.get('codedGameState', None)
        self.statusCode = status.get('statusCode', None)
        self.abstractGameCode = status.get('abstractGameCode', None)

        # Handle game_state easily
        if self.statusCode in ('IO', 'IR', 'PI', 'PR', 'PY'):
            self.game_state = 'D' # Delayed
        elif self.statusCode in ('TR', 'UR', 'DC', 'DR', 'DI'):
            self.game_state = 'S' # Suspended/Postponed
        elif self.codedGameState in ('S', 'P'):
            self.game_state = 'P' # Pre-game
        elif self.codedGameState in ('I', 'M', 'N'):
            self.game_state = 'L' # Live
        elif self.codedGameState in ('F', 'O'):
            self.game_state = 'F' # Final
        else:
            self.game_state = 'U' # Unknown
        # no children

    def __repr__(self):
        return self.detailedState


class TeamsGameData:
    def __init__(self, teams):
        self.away = teams['away']
        self.home = teams['home']
        self._children()

    def _children(self):
        self.away = TeamGameData(self.away)
        self.home = TeamGameData(self.home)

    def __repr__(self):
        away_team = self.away.abbreviation
        home_team = self.home.abbreviation

        return f'{away_team} at {home_team}'


class TeamGameData:
    def __init__(self, team):
        self.id = team['id']
        self.abbreviation = team['abbreviation']
        self.teamName = team['teamName']
        self.division = _get_division(self.id)
        # no children

    def __repr__(self):
        return self.abbreviation


class Weather:
    def __init__(self, weather):
        self.condition = weather.get('condition', None)
        self.temp = weather.get('temp', None)
        self.wind = weather.get('wind', None)
        # no children

    def __repr__(self):
        temp = self.temp
        condition = self.condition

        return f'{temp}F, {condition}'


class GameInfo:
    def __init__(self, gameInfo):
        self.attendance = gameInfo.get('attendance', None)
        self.firstPitch = gameInfo.get('firstPitch', None)
        self.gameDurationMinutes = gameInfo.get('gameDurationMinutes', None)
        # no children


class Flags:
    def __init__(self, flags):
        self.noHitter = flags['noHitter']
        self.perfectGame = flags['perfectGame']
        # no children


class OfficialScorer:
    def __init__(self, officialScorer):
        self.id = officialScorer['id']
        self.fullName = officialScorer['fullName']
        self.link = officialScorer['link']
        # no children

    def __repr__(self):
        return self.fullName


class PrimaryDatacaster:
    def __init__(self, primaryDatacaster):
        self.id = primaryDatacaster['id']
        self.fullName = primaryDatacaster['fullName']
        self.link = primaryDatacaster['link']
        # no children

    def __repr__(self):
        return self.fullName


class LiveData:
    def __init__(self, liveData):
        self._liveData = liveData
        self.plays = liveData['plays']
        self.linescore = liveData['linescore']
        self.boxscore = liveData['boxscore']
        self.decisions = liveData.get('decision', {})
        self._children()

    def _children(self):
        self.plays = Plays(self.plays)
        self.linescore = Linescore(self.linescore)

    def __eq__(self, other):
        if self._liveData == other._liveData:
            return True
        return False


class Plays:
    def __init__(self, plays):
        self._test = plays
        self.allPlays: List[AllPlays] = [AllPlays(play) for play in plays['allPlays']]
        self.currentPlay = plays.get('currentPlay', None)


class AllPlays:
    """
    Holds data for each at bat
    """
    def __init__(self, allPlays: dict):
        self._allPlays = allPlays
        self.result = allPlays.get('result', None)
        self.about = allPlays.get('about', None)
        self.count = allPlays.get('count', None)
        self.matchup = allPlays.get('matchup', None)
        self.pitchIndex = allPlays.get('pitchIndex', None)
        events = allPlays.get('playEvents', None)
        self.playEvents: List[PlayEvents] = [PlayEvents(i) for i in events]
        self.playEndTime = allPlays.get('playEndTime', None)
        self.atBatIndex = allPlays.get('atBatIndex', None)
        self._children()

    def _children(self):
        self.result = Result(self.result)
        self.about = About(self.about)
        self.count = Count(self.count)
        self.matchup = Matchup(self.matchup)

    def __eq__(self, other):
        if self._allPlays == other._allPlays:
            return True
        return False

    def __repr__(self):
        pitcher = self.matchup.pitcher.fullName
        batter = self.matchup.batter.fullName
        return f'{pitcher} to {batter}'


class Result:
    def __init__(self, result):
        self.type = result['type']
        self.event = result.get('event', None)
        self.eventType = result.get('eventType')
        self.description = result.get('description')
        self.rbi = result.get('rbi', None)
        self.awayScore = result.get('awayScore', None)
        self.homeScore = result.get('homeScore', None)
        self.isOut = result.get('isOut', None)
        # no children


class About:
    def __init__(self, about):
        self.atBatIndex = about['atBatIndex']
        self.halfInning: str = about['halfInning']
        self.isTopInning = bool(about['isTopInning'])
        self.inning = int(about['inning'])
        self.startTime = about.get('startTime', None)
        self.endTime = about['endTime']
        self.isComplete = about['isComplete']
        self.isScoringPlay = about.get('isScoringPlay', None)
        self.hasReview = about.get('hasReview', None)
        self.hasOut = about.get('hasOut', None)
        self.captivatingIndex = about.get('captivatingIndex', None)
        # no children


class Count:
    def __init__(self, count):
        self.balls = int(count.get('balls', None))
        self.strikes = int(count.get('strikes', None))
        self.outs = int(count.get('outs', None))
        # no children

    def __repr__(self):
        return f'{self.balls}-{self.strikes} {self.outs} outs'


class Matchup:
    def __init__(self, matchup):
        self.batter = matchup['batter']
        self.batSide = matchup['batSide']
        self.pitcher = matchup['pitcher']
        self.pitchHand = matchup['pitchHand']
        self.postOnFirst = matchup.get('postOnFirst', None)
        self.postOnSecond = matchup.get('postOnSecond', None)
        self.postOnThird = matchup.get('postOnThird', None)
        self.splits = matchup.get('splits', None)

        self._children()

    def _children(self):
        self.batter = Player(self.batter)
        self.batSide = Side(self.batSide)
        self.pitcher = Player(self.pitcher)
        self.pitchHand = Side(self.pitchHand)

        if self.postOnFirst is not None:
            self.postOnFirst = Player(self.postOnFirst)

        if self.postOnSecond is not None:
            self.postOnSecond = Player(self.postOnSecond)

        if self.postOnThird is not None:
            self.postOnThird = Player(self.postOnThird)

        if self.splits is not None:
            self.splits = Splits(self.splits)


class Side:
    def __init__(self, side):
        self.code = side.get('L', None)
        self.description = side['description']


class Splits:
    def __init__(self, splits):
        self.batter = splits.get('batter', None)
        self.pitcher = splits.get('pitcher', None)
        self.menOnBase = splits.get('menOnBase', None)


class PlayEvents:
    MOE = MARGIN_OF_ERROR
    rednp = get_run_expectency_difference_numpy()

    def __init__(self, playEvents: dict):
        self._playEvents = playEvents
        self.details = playEvents.get('details', None)
        self.count = playEvents.get('count', None)
        self.pitchData = playEvents.get('pitchData', None)
        self.hitData = playEvents.get('hitData', None)
        self.index = playEvents.get('index', None)
        self.playId = playEvents.get('playId', None)
        self.pitchNumber = playEvents.get('pitchNumber', None)
        self.startTime = playEvents.get('startTime', None)
        self.endTime = playEvents.get('endTime', None)
        self.isPitch = bool(playEvents.get('isPitch', None))
        self.type = playEvents.get('type', None)

        if self.pitchNumber is not None:
            self.pitchNumber = int(self.pitchNumber)

        if self.index is not None:
            self.index = int(self.index)

        self._children()

    def _children(self):
        if self.details is not None:
            self.details = Details(self.details)

        if self.count is not None:
            self.count = Count(self.count)

        if self.hitData is not None:
            self.hitData = HitData(self.hitData)

        if self.pitchData is not None:
            self.pitchData = PitchData(self.pitchData)

    def __eq__(self, other):
        if other is None:
            return False
        if self._playEvents == other._playEvents:
            return True
        return False


class Details:
    def __init__(self, details):
        self.call = details.get('call', None)
        self.description = details.get('description', None)
        self.event = details.get('event', None)
        self.eventType = details.get('eventType', None)
        #self.awayScore = int(details.get('awayScore', None))
        #self.homeScore = int(details.get('homeScore', None))
        self.code = details.get('code', None)
        self.ballColor = details.get('ballColor', None)
        self.trailColor = details.get('trailColor', None)
        self.isInPlay = bool(details.get('isPitch', None))
        self.isStrike = bool(details.get('isStrike', None))
        self.isBall = bool(details.get('isBall', None))
        self.type = details.get('type', None)
        self.isOut = bool(details.get('isOut', None))
        self.hasReview = bool(details.get('hasReview', None))
        self._children()

    def _children(self):
        if self.type:
            self.type = PitchType(self.type)


class PitchType:
    def __init__(self, pitchType):
        self.code = pitchType.get('code', None)
        self.description = pitchType.get('description', None)
        # no children


class PitchData:
    def __init__(self, pitchData):
        self._pitchData = pitchData
        self.startSpeed = pitchData.get('startSpeed', None)
        self.endSpeed = pitchData.get('endSpeed', None)
        self._sz_top = float(pitchData.get('strikeZoneTop', None))
        self._sz_bot = float(pitchData.get('strikeZoneBottom', None))
        self.coordinates = pitchData.get('coordinates')
        self.breaks = pitchData.get('breaks', None)
        self.zone = pitchData.get('zone', None)
        self.typeConfindence = pitchData.get('typeConfidence', None)
        self.plateTime = pitchData.get('plateTime', None)
        self.extension = pitchData.get('extension', None)

        if self.startSpeed is not None:
            self.startSpeed = float(self.startSpeed)

        if self.endSpeed is not None:
            self.endSpeed = float(self.endSpeed)

        if self.zone is not None:
            self.zone = int(self.zone)

        if self.plateTime is not None:
            self.plateTime = float(self.plateTime)

        self._children()

    def _children(self):
        if self.coordinates is not None:
            self.coordinates = PitchCoordinates(self.coordinates, self._sz_top, self._sz_bot)

        if self.breaks:
            self.breaks = Breaks(self.breaks)

    def __str__(self):
        # Bother with margin of error?
        if self.zone >= 1 and self.zone <= 9:
            return 'In Zone'
        else:
            return 'Out of Zone'


class PitchCoordinates:
    BALL_CIRCUMFERENCE_INCH = 9.125
    BALL_RADIUS_INCH = BALL_CIRCUMFERENCE_INCH / (2 * math.pi)
    BALL_RADIUS_FEET = BALL_RADIUS_INCH / 12

    PLATE_WIDTH_INCH = 17
    PLATE_WIDTH_FEET = PLATE_WIDTH_INCH / 12
    PX_MIN = (-PLATE_WIDTH_FEET / 2) - BALL_RADIUS_FEET
    PX_MAX = (PLATE_WIDTH_FEET / 2) + BALL_RADIUS_FEET

    def __init__(self, coor, sz_top, sz_bot):

        # Strike Zone top and bottom
        self.sZ_top = sz_top
        self.sZ_bot = sz_bot

        # Location of Center of Pitch for Ball/Strike
        self.pZ_top = self.sZ_top + self.BALL_RADIUS_FEET
        self.pZ_bot = self.sZ_bot - self.BALL_RADIUS_FEET

        # Acceleration in X,Y,Z directions
        self.aX = coor.get('aX', None)
        self.aY = coor.get('aY', None)
        self.aZ = coor.get('aZ', None)

        if self.aX is not None:
            self.aX = float(self.aX)

        if self.aY is not None:
            self.aY = float(self.aY)

        if self.aZ is not None:
            self.aZ = float(self.aZ)

        # Movement of Pitch at y=40ft
        self.pfxX = coor.get('pfxX', None)
        self.pfxZ = coor.get('pfxZ', None)

        if self.pfxX is not None:
            self.pfxX = float(self.pfxX)

        if self.pfxZ is not None:
            self.pfxZ = float(self.pfxZ)

        # Pitch Location
        self.pX = coor.get('pX', None)
        self.pZ = coor.get('pZ', None)

        if self.pX is not None:
            self.pX = float(self.pX)

        if self.pZ is not None:
            self.pZ = float(self.pZ)

        # Velocity of Pitch at Release in X,Y,Z directions
        self.vX0 = coor.get('vX0', None)
        self.vY0 = coor.get('vY0', None)
        self.vZ0 = coor.get('vZ0', None)

        if self.vX0 is not None:
            self.vX0 = float(self.vX0)

        if self.vY0 is not None:
            self.vY0 = float(self.vY0)

        if self.vZ0 is not None:
            self.vZ0 = float(self.vZ0)

        # Old Pitch Location Data
        self.x = coor.get('x', None)
        self.y = coor.get('y', None)

        if self.x:
            self.x = float(self.x)
        if self.y:
            self.y = float(self.y)

        # Position of Pitch at Release in X,Y,Z directions
        self.x0 = coor.get('x0', None)
        self.y0 = coor.get('y0', None)
        self.z0 = coor.get('z0', None)

        if self.x0 is not None:
            self.x0 = float(self.x0)

        if self.y0 is not None:
            self.y0 = float(self.y0)

        if self.z0 is not None:
            self.z0 = float(self.z0)

        #self.above_zone = self.pZ - self.pZ_top
        #self.below_zone = self.pZ_bot - self.pZ

        # no children

    def is_valid(self) -> bool:
        if self.pX is not None and self.pZ is not None:
            return True
        elif self.pX is None or self.pZ is None:
            return False


class Breaks:
    def __init__(self, breaks):
        self.breakAngle = breaks.get('breakAngle', None)
        self.spinRate = breaks.get('spinRate', None)
        self.spinDirection = breaks.get('spinDirection', None)
        # no children


class HitData:
    def __init__(self, hitData):
        self.launchSpeed = hitData.get('launchSpeed', None)
        self.launchAngle = hitData.get('launchAngle', None)
        self.totalDistance = hitData.get('totalDistance', None)
        self.trajectory = hitData.get('trajectory', None)
        self.hardness = hitData.get('hardness', None)
        self.location = hitData.get('location', None)
        self.coordinates = hitData.get('coordinates', None)

        if self.launchSpeed:
            self.launchSpeed = float(self.launchSpeed)

        if self.launchAngle:
            self.launchAngle = float(self.launchAngle)

        if self.totalDistance:
            self.totalDistance = float(self.totalDistance)
        self._children()

    def _children(self):
        self.coordinates = HitCoordinates(self.coordinates)


class HitCoordinates:
    def __init__(self, coor):
        self.coordX = coor.get('coordX', None)
        self.coordY = coor.get('coordY', None)


class Linescore:
    def __init__(self, linescore):
        self.currentInning = linescore.get('currentInning', None)
        self.currentInningOrdinal = linescore.get('currentInningOrdinal', None)
        self.inningState = linescore.get('inningState', None)
        self.inningHalf = linescore.get('inningHalf', None)
        self.isTopInning = linescore.get('isTopInning', None)
        self.scheduledInnings = linescore.get('scheduledInnings', None)
        self.teams = linescore['teams']
        self.defense = linescore['defense']
        self.offense = linescore['offense']
        self.balls = linescore.get('balls', None)
        self.strikes = linescore.get('strikes', None)
        self.outs = linescore.get('outs', None)
        self._children()

    def _children(self):
        self.teams = TeamsLinescore(self.teams)
        self.defense = Defense(self.defense)
        self.offense = Offense(self.offense)

    def __repr__(self):
        inn_state = self.inningState
        inning = self.currentInningOrdinal

        away_score = self.teams.away.runs
        home_score = self.teams.home.runs

        return f'{inn_state} {inning}. {away_score}-{home_score}'


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


class Defense:
    def __init__(self, defense):
        self.pitcher = defense.get('pitcher', None)
        self.catcher = defense.get('catcher', None)
        self.first = defense.get('first', None)
        self.second = defense.get('second', None)
        self.third = defense.get('third', None)
        self.shortstop = defense.get('shortstop', None)
        self.left = defense.get('left', None)
        self.center = defense.get('center', None)
        self.right = defense.get('right', None)
        self.batter = defense.get('batter', None)
        self.onDeck = defense.get('onDeck', None)
        self.inHole = defense.get('inHole', None)
        self.battingOrder = defense.get('battingOrder', None)
        self.team = defense.get('team', None)
        self._children()

    def _children(self):
        if self.pitcher:
            self.pitcher = Player(self.pitcher)

        if self.catcher:
            self.catcher = Player(self.catcher)

        if self.first:
            self.first = Player(self.first)

        # continue with other positions + batter,ondeck,inhole


class Offense:
    def __init__(self, offense):
        self.batter = offense.get('batter', None)
        self.onDeck = offense.get('onDeck', None)
        self.inHole = offense.get('inHole', None)
        self.first = offense.get('first', None)
        self.second = offense.get('second', None)
        self.third = offense.get('third', None)
        self.pitcher = offense.get('pitcher', None)

        self.is_first = True if self.first is not None else False
        self.is_second = True if self.second is not None else False
        self.is_third = True if self.third is not None else False
        #runners_list = [self.is_first, self.is_second, self.is_third]

        self._children()

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
        self.id = player.get('id', None)
        self.fullName = player.get('fullName', None)
        self.link = player.get('link', None)
        # no children


class Decisions:
    def __init__(self, decision):
        self.winner = decision['winner']
        self.loser = decision['loser']
        self._children()

    def _children(self):
        self.winner = Player(self.winner)
        self.loser = Player(self.loser)


def _convert_zulu_to_local(zulu_time_str) -> Tuple[int, int]:
    zulu_time = datetime.datetime.strptime(zulu_time_str, '%Y-%m-%dT%H:%M:%SZ')
    zulu_time = pytz.utc.localize(zulu_time)

    local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    local_time = zulu_time.astimezone(local_timezone)

    t = local_time.strftime('%I:%M')

    if t[0] == str('0'):
        t = f' {t[1:]}'

    t = f'{t[0:2]} {t[3:]}'

    return (int(t[0:2]), int(t[3:]))


def _get_division(code:int):
    if (108 == code): # LAA
        return 'AW'
    if (109 == code): # ARI
      return 'NW'
    if (110 == code): # BAL
      return 'AE'
    if (111 == code): # BOS
      return 'AE'
    if (112 == code): # CHC
      return 'NC'
    if (113 == code): # CIN
      return 'NC'
    if (114 == code): # CLE
      return 'AC'
    if (115 == code): # COL
      return 'NW'
    if (116 == code): # DET
      return 'AC'
    if (117 == code): # HOU
      return 'AW'
    if (118 == code): # KC
      return 'AC'
    if (119 == code): # LAD
      return 'NW'
    if (120 == code): # WSH
      return 'NE'
    if (121 == code): # NYM
      return 'NE'
    if (133 == code): # OAK
      return 'AW'
    if (134 == code): # PIT
      return 'NC'
    if (135 == code): # SD
      return 'NW'
    if (136 == code): # SEA
      return 'AW'
    if (137 == code): # SF
      return 'NW'
    if (138 == code): # STL
      return 'NC'
    if (139 == code): # TB
      return 'AE'
    if (140 == code): # TEX
      return 'AW'
    if (141 == code): # TOR
      return 'AE'
    if (142 == code): # MIN
      return 'AC'
    if (143 == code): # PHI
      return 'NE'
    if (144 == code): # ATL
      return 'NE'
    if (145 == code): # CHW
      return 'AC'
    if (146 == code): # MIA
      return 'NE'
    if (147 == code): # NYY
      return 'AE'
    if (158 == code): # MIL
      return 'NC'


def get_games() -> List[Game]:
    gamepks = get_daily_gamepks()
    games = []

    for pk in tqdm(gamepks):
        data = statsapi.get('game', {'gamePk': pk})
        games.append(Game(data))

    return games


if __name__ == "__main__":
    game = Game.get_game_from_pk(gamepk = 717200, delay_seconds = 0)
