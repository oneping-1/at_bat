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
from typing import List, Tuple, Union
import math
from datetime import datetime, timedelta, timezone
import requests
from tzlocal import get_localzone
import pytz
import statsapi # pylint: disable=E0401
from tqdm import tqdm
from dateutil import tz
from at_bat.statsapi_plus import get_daily_gamepks
from time import sleep

MARGIN_OF_ERROR = 0.25/12 # Margin of Error of hawkeye system (inches)

# Update for new game states for custom game_state attribute
KNOWN_GAMESTATES = ('S','P','PI','PL','PO','PR','PY','PW','I','IO','IR',
                    'MA','MB','MC','MD','ME','MF','MG','MH','MI','MJ',
                    'MM','MN','MO','MP','MS','MT','MU','MV','MQ','MW',
                    'MX','MY','NA','NF','NJ','NI','NK','NN','NO','NH',
                    'NQ','TR','UR','O','OO','OR','F','FG','FO','FR',
                    'FT','DI','DC','DR','CR','CG','CI')

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

        time = datetime.now(get_localzone()).isoformat()

        with open(path, 'a', encoding='utf-8') as file:
            file.write(f'gamepk: {self.gamepk}\n')
            file.write(f'time: {time}\n')
            file.write(f'away: {self.gameData.teams.away.abbreviation}\n')
            file.write(f'home: {self.gameData.teams.home.abbreviation}\n')
            file.write(f'inningState: {self.liveData.linescore.inningState}\n')
            file.write(f'inning: {self.liveData.linescore.currentInning}\n')
            file.write(f'outs: {self.liveData.linescore.outs}\n')
            file.write(f'astractGameState: {abstractGameState}\n')
            file.write(f'abstractGameCode: {abstractGameCode}\n')
            file.write(f'detailedState: {detailedState}\n')
            file.write(f'codedGameState: {codedGameState}\n')
            file.write(f'statusCode: {statusCode}\n')
            file.write('\n')

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

        game_dict = cls.get_dict(gamepk=gamepk, delay_seconds=delay_seconds)
        return Game(game_dict)

    @classmethod
    def get_dict(cls, gamepk: int = None, time: Union[str, None] = None,
        delay_seconds: Union[int, None] = 0) -> dict:
        """
        Returns the game data for a given gamePk. If time is provided, the game
        data at that time is returned. If time is not provided, the game data
        at the current time is returned.

        Args:
            gamepk (int): gamepk for the desired game. Defaults to None.
            time (str, optional): time (ISO 8601). Defaults to None.
            delay_seconds (int, optional): number of seconds to be delayed.
                Defaults to 0.

        Raises:
            ValueError: No gamepk  provided
            MaxRetriesError: Max retries reached

        Returns:
            dict: The game data for the given gamePk
        """
        max_retries = 10

        if gamepk is None:
            raise ValueError('gamePk not provided')

        if time is not None:
            delay_time = _get_utc_time_from_zulu(time)
        else:
            delay_time = _get_utc_time(delay_seconds=delay_seconds)

        for i in range(max_retries):
            try:
                data = statsapi.get('game',
                    {'gamePk': gamepk, 'timecode': delay_time},
                    force=True)
                return data
            except requests.exceptions.RequestException as e:
                print(f'ReadTimeout ({i+1}/{max_retries})')
                print(f'Error: {e}')
                sleep(min(2**i, 30))  # Exponential backoff

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
        self.venue = gameData['venue']
        self.weather = gameData.get('weather', None)
        self.gameInfo = gameData.get('gameInfo', None)
        self.flags = gameData.get('flags', None)
        self.probablePitchers = gameData.get('probablePitchers', None)
        self.officialScorer = gameData.get('officialScorer', None)
        self.primaryDatacaster = gameData.get('primaryDatacaster', None)
        self._children()

    def _children(self):
        self.datetime = Datetime(self.datetime)
        self.status = Status(self.status)
        self.teams = TeamsGameData(self.teams)
        self.venue = Venue(self.venue)

        if self.weather is not None:
            self.weather = Weather(self.weather)

        if self.gameInfo is not None:
            self.gameInfo = GameInfo(self.gameInfo)

        if self.flags is not None:
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
        if start_time is None:
            self.startHour = 0
            self.startMinute = 0
        else:
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
        if self.statusCode in ('IO','IR','PI','PL','PO','PR','PY'):
            self.game_state = 'D' # Delayed
        elif self.statusCode in ('TR','UR','DC','DR','DI'):
            self.game_state = 'S' # Suspended/Postponed
        elif self.codedGameState in ('S','P'):
            self.game_state = 'P' # Pre-game
        elif self.codedGameState in ('I','M','N'):
            self.game_state = 'L' # Live
        elif self.codedGameState in ('F','O'):
            self.game_state = 'F' # Final
        elif self.codedGameState == 'C':
            self.game_state = 'C' # Cancelled
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
        self.location_name = team['locationName']
        self.division = _get_division(self.abbreviation)
        # no children

    def __repr__(self):
        return self.abbreviation


class Venue:
    def __init__(self, venue):
        self.id: int = venue.get('id', None)
        self.name: str = venue.get('name', None)
        self.link: str = venue.get('link', None)
        self.location = venue.get('location', None)
        self.timeZone = venue.get('timeZone', None)
        self.fieldInfo = venue.get('fieldInfo', None)
        self.active: bool = venue.get('active', None)
        self.season: int = venue.get('season', None)

        self._children()

    def _children(self):
        if self.location is not None:
            self.location = Location(self.location)

        if self.timeZone is not None:
            self.timeZone = TimeZone(self.timeZone)

        if self.fieldInfo is not None:
            self.fieldInfo = FieldInfo(self.fieldInfo)


class Location:
    def __init__(self, location):
        self.address1: str = location.get('address1', None)
        self.address2: str = location.get('address2', None)
        self.city: str = location.get('city', None)
        self.state: str = location.get('state', None)
        self.stateAbbrev: str = location.get('stateAbbrev', None)
        self.postalCode: str = location.get('postalCode', None)
        self.defaultCoordinates = location.get('defaultCoordinates', None)
        self.azimuthAngle: float = location.get('azimuthAngle', None)
        self.elevation: int = location.get('elevation')
        self.country: str = location.get('country')
        self.phone: str = location.get('phone')

    def _children(self):
        self.defaultCoordinates = DefaultCoordinates(self.defaultCoordinates)


class DefaultCoordinates:
    def __init__(self, defaultCoordinates):
        self.latitude: float = defaultCoordinates.get('latitude', None)
        self.longitude: float = defaultCoordinates.get('longitude', None)


class TimeZone:
    def __init__(self, timeZone):
        self.id: str = timeZone.get('id', None)
        self.offset: int = timeZone.get('offset', None)
        self.offsetAtGameTime: int = timeZone.get('offsetAtGameTime', None)
        self.tz: str = timeZone.get('tz', None)


class FieldInfo:
    def __init__(self, fieldInfo):
        self.capacity: int = fieldInfo.get('capacity', None)
        self.turfType: str = fieldInfo.get('turfType', None)
        self.roofType: str = fieldInfo.get('roofType', None)
        self.leftLine: int = fieldInfo.get('leftLine', None)
        self.left: int = fieldInfo.get('left', None)
        self.leftCenter: int = fieldInfo.get('leftCenter', None)
        self.center: int = fieldInfo.get('center', None)
        self.rightCenter: int = fieldInfo.get('rightCenter', None)
        self.right: int = fieldInfo.get('right', None)
        self.rightLine: int = fieldInfo.get('rightLine', None)


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
        self.no_hitter = flags.get('noHitter', None)
        self.perfect_game = flags.get('perfectGame', None)
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
        self.plays = liveData.get('plays', None)
        self.linescore = liveData.get('linescore', None)
        self.boxscore = liveData.get('boxscore', None)
        self.decisions = liveData.get('decisions', None)
        self._children()

    def _children(self):
        if self.plays is not None:
            self.plays = Plays(self.plays)

        if self.linescore is not None:
            self.linescore = Linescore(self.linescore)

        if self.boxscore is not None:
            self.boxscore = Boxscore(self.boxscore)

        if self.decisions is not None:
            self.decisions = Decisions(self.decisions)

    def __eq__(self, other):
        if self._liveData == other._liveData:
            return True
        return False


class Plays:
    def __init__(self, plays):
        self._test = plays
        self.allPlays: List[AllPlays] = [AllPlays(play) for play in plays['allPlays']]
        self.currentPlay = plays.get('currentPlay', None)
        self._children()

    def _children(self):
        if self.currentPlay is not None:
            self.currentPlay = AllPlays(self.currentPlay)


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
        self.actionIndex: List[int] = allPlays.get('actionIndex', None)
        self.runners = allPlays.get('runners', None)
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
        self.runners = [RunnersMovement(runner) for runner in self.runners]

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


class RunnersMovement:
    def __init__(self, runners):
        self.movement = runners.get('movement', None)
        self.details = runners.get('details', None)
        self.create = runners.get('create', None)
        self._children()

    def _children(self):
        self.movement = Movement(self.movement)
        self.details = RunnersDetails(self.details)


class Movement:
    def __init__(self, movement):
        self.originBase = movement.get('originBase', None)
        self.start = movement.get('start', None)
        self.end = movement.get('end', None)
        self.outBase = movement.get('outBase', None)
        self.isOut = movement.get('isOut', None)
        self.outNumber = movement.get('outNumber', None)

        if self.originBase is not None:
            self.originBaseNum = int(self.originBase[0])
        else:
            self.originBaseNum = None

        if self.start is not None:
            self.startNum = int(self.start[0])
        else:
            self.startNum = None

        if self.end in ('score', 'home'):
            self.endNum = 4
        elif self.end is not None:
            self.endNum = int(self.end[0])
        else:
            self.endNum = None

        if self.outBase is not None:
            self.outBaseNum = int(self.outBase[0])
        else:
            self.outBaseNum = None


class RunnersDetails:
    def __init__(self, details):
        self.event = details.get('event', None)
        self.eventType = details.get('eventType', None)
        self.movementReason = details.get('movementReason', None)
        self.runner = details.get('runner', None)
        self.responsiblePitcher = details.get('responsiblePitcher', None)
        self.isScoringEvent = details.get('isScoringEvent', None)
        self.rbi = details.get('rbi', None)
        self.earned = details.get('earned', None)
        self.teamUnearned = details.get('teamUnearned', None)
        self.playIndex = details.get('playIndex', None)


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
        self.isBaseRunningPlay = bool(playEvents.get('isBaseRunningPlay', None))
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

    def __repr__(self):
        return self.details.description


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
        self.isPitch = bool(details.get('isPitch', None))
        self.isBaseRunningPlay = bool(details.get('isBaseRunningPlay', None))
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
        self.typeConfidence = pitchData.get('typeConfidence', None)
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
        self.pZ_max = self.sZ_top + self.BALL_RADIUS_FEET
        self.pZ_min = self.sZ_bot - self.BALL_RADIUS_FEET

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
        if (self.pX is not None) and (self.pZ is not None):
            return True
        return False


class Breaks:
    def __init__(self, breaks):
        self.breakAngle = breaks.get('breakAngle', None)
        self.breakLength = breaks.get('breakLength', None)
        self.breakY = breaks.get('breakY', None)
        self.breakVertical = breaks.get('breakVertical', None)
        self.breakVerticalInduced = breaks.get('breakVerticalInduced', None)
        self.breakHorizontal = breaks.get('breakHorizontal', None)
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
        self.innings = linescore.get('innings', None)
        self.teams = linescore.get('teams', None)
        self.defense = linescore.get('defense', None)
        self.offense = linescore.get('offense', None)
        self.balls = linescore.get('balls', None)
        self.strikes = linescore.get('strikes', None)
        self.outs = linescore.get('outs', None)
        self._children()

    def _children(self):
        if self.innings is not None:
            self.innings = [Inning(inning) for inning in self.innings]

        if self.teams is not None:
            self.teams = TeamsLinescore(self.teams)

        if self.defense is not None:
            self.defense = Defense(self.defense)

        if self.offense is not None:
            self.offense = Offense(self.offense)

    def __repr__(self):
        inn_state = self.inningState
        inning = self.currentInningOrdinal

        away_score = self.teams.away.runs
        home_score = self.teams.home.runs

        return f'{inn_state} {inning}. {away_score}-{home_score}'


class Inning:
    def __init__(self, inning):
        self.num = inning.get('num', None)
        self.ordinalNum = inning.get('ordinalNum', None)
        self.home = inning.get('home', None)
        self.away = inning.get('away', None)
        self._children()

    def _children(self):
        self.away = TeamInning(self.away)
        self.home = TeamInning(self.home)


class TeamInning:
    def __init__(self, teamInning):
        self.runs = teamInning.get('runs', None)
        self.hits = teamInning.get('hits', None)
        self.errors = teamInning.get('errors', None)
        # no children


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
        self.left_on_base = team.get('leftOnBase', None)
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

        self.batting_order: int = offense.get('battingOrder', None)

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
        if player is None:
            self.id = None
            self.fullName = None
            self.link = None
            return

        self.id = player.get('id', None)
        self.fullName = player.get('fullName', None)
        self.link = player.get('link', None)
        # no children


class Boxscore:
    def __init__(self, boxscore):
        self.teams = boxscore['teams']
        self.officials = boxscore.get('officials', None)
        self.pitchingNotes = boxscore.get('pitchingNotes', None)
        self.top_performers = boxscore.get('top_performers', None)
        self._children()

    def _children(self):
        self.teams = TeamsBoxScore(self.teams)


class TeamsBoxScore:
    def __init__(self, team_box_score):
        self.away = team_box_score['away']
        self.home = team_box_score['home']
        self._children()

    def _children(self):
        self.away = TeamBoxScore(self.away)
        self.home = TeamBoxScore(self.home)



class TeamBoxScore:
    def __init__(self, team_box_score):
        self.team = team_box_score.get('team', None)
        self.team_stats = team_box_score.get('teamStats', None)
        self.players: List[dict] = team_box_score.get('players', None)
        self.batters: List[int] = team_box_score.get('batters', None)
        self.pitchers: List[int] = team_box_score.get('pitchers', None)
        self.bench: List[int] = team_box_score.get('bench', None)
        self.bullpen: List[int] = team_box_score.get('bullpen', None)
        self.batting_order: List[int] = team_box_score.get('battingOrder', None)
        self.info = team_box_score.get('info', None)
        self.note = team_box_score.get('note', None)
        self._children()

    def _children(self):
        self.team = TeamBoxScoreTeam(self.team)


class TeamBoxScoreTeam:
    def __init__(self, team_box_score_team):
        self.all_star_status = team_box_score_team.get('allStarStatus', None)
        self.id = team_box_score_team.get('id', None)
        self.name = team_box_score_team.get('name', None)
        self.link = team_box_score_team.get('link', None)


class TeamStats:
    def __init__(self, team_stats):
        self.batting = team_stats.get('batting', None)
        self.pitching = team_stats.get('pitching', None)
        self.fielding = team_stats.get('fielding', None)
        self._children()

    def _children(self):
        self.batting = BattingStats(self.batting)
        self.pitching = PitchingStats(self.pitching)
        self.fielding = FieldingStats(self.fielding)


class BattingStats:
    def __init__(self, batting_stats):
        self.fly_outs = batting_stats.get('flyOuts', None)
        self.ground_outs = batting_stats.get('groundOuts', None)
        self.air_outs = batting_stats.get('airOuts', None)
        self.runs = batting_stats.get('runs', None)
        self.doubles = batting_stats.get('doubles', None)
        self.triples = batting_stats.get('triples', None)
        self.home_runs = batting_stats.get('homeRuns', None)
        self.strike_outs = batting_stats.get('strikeOuts', None)
        self.base_on_balls = batting_stats.get('baseOnBalls', None)
        self.intentional_walks = batting_stats.get('intentionalWalks', None)
        self.hits = batting_stats.get('hits', None)
        self.hit_by_pitch = batting_stats.get('hitByPitch', None)
        self.avg = batting_stats.get('avg', None)
        self.at_bats = batting_stats.get('atBats', None)
        self.obp = batting_stats.get('obp', None)
        self.slg = batting_stats.get('slg', None)
        self.ops = batting_stats.get('ops', None)
        self.caught_stealing = batting_stats.get('caughtStealing', None)
        self.stolen_bases = batting_stats.get('stolenBases', None)
        self.stolen_base_percentage = batting_stats.get('stolenBasePercentage', None)
        self.ground_into_double_play = batting_stats.get('groundIntoDoublePlay', None)
        self.ground_into_triple_play = batting_stats.get('groundIntoTriplePlay', None)
        self.plate_appearances = batting_stats.get('plateAppearances', None)
        self.total_bases = batting_stats.get('totalBases', None)
        self.rbi = batting_stats.get('rbi', None)
        self.left_on_base = batting_stats.get('leftOnBase', None)
        self.sac_bunts = batting_stats.get('sacBunts', None)
        self.sac_flies = batting_stats.get('sacFlies', None)
        self.catchers_interference = batting_stats.get('catchersInterference', None)
        self.pickoffs = batting_stats.get('pickoffs', None)
        self.at_bats_per_home_run = batting_stats.get('atBatsPerHomeRun', None)
        self.pop_outs = batting_stats.get('popOuts', None)
        self.line_outs = batting_stats.get('lineOuts', None)
        # no children


class PitchingStats:
    def __init__(self, pitching_stats):
        self.fly_outs = pitching_stats.get('flyOuts', None)
        self.ground_outs = pitching_stats.get('groundOuts', None)
        self.air_outs = pitching_stats.get('airOuts', None)
        self.runs = pitching_stats.get('runs', None)
        self.doubles = pitching_stats.get('doubles', None)
        self.triples = pitching_stats.get('triples', None)
        self.home_runs = pitching_stats.get('homeRuns', None)
        self.strike_outs = pitching_stats.get('strikeOuts', None)
        self.base_on_balls = pitching_stats.get('baseOnBalls', None)
        self.intentional_walks = pitching_stats.get('intentionalWalks', None)
        self.hits = pitching_stats.get('hits', None)
        self.hit_by_pitch = pitching_stats.get('hitByPitch', None)
        self.at_bats = pitching_stats.get('atBats', None)
        self.obp = pitching_stats.get('obp', None)
        self.caught_stealing = pitching_stats.get('caughtStealing', None)
        self.stolen_bases = pitching_stats.get('stolenBases', None)
        self.stolen_base_percentage = pitching_stats.get('stolenBasePercentage', None)
        self.number_of_pitches = pitching_stats.get('numberOfPitches', None)
        self.era = pitching_stats.get('era', None)
        self.innings_pitched = pitching_stats.get('inningsPitched', None)
        self.save_opportunities = pitching_stats.get('saveOpportunities', None)
        self.earned_runs = pitching_stats.get('earnedRuns', None)
        self.whip = pitching_stats.get('whip', None)
        self.batters_faced = pitching_stats.get('battersFaced', None)
        self.outs = pitching_stats.get('outs', None)
        self.complete_games = pitching_stats.get('completeGames', None)
        self.shutouts = pitching_stats.get('shutouts', None)
        self.pitches_thrown = pitching_stats.get('pitchesThrown', None)
        self.balls = pitching_stats.get('balls', None)
        self.strikes = pitching_stats.get('strikes', None)
        self.strike_percentage = pitching_stats.get('strikePercentage', None)
        self.hit_batsmen = pitching_stats.get('hitBatsmen', None)
        self.balks = pitching_stats.get('balks', None)
        self.wild_pitches = pitching_stats.get('wildPitches', None)
        self.pickoffs = pitching_stats.get('pickoffs', None)
        self.ground_outs_to_airouts = pitching_stats.get('groundOutsToAirouts', None)
        self.rbi = pitching_stats.get('rbi', None)
        self.pitches_per_innning = pitching_stats.get('pitchesPerInning', None)
        self.runs_scored_per_9 = pitching_stats.get('runsScoredPer9', None)
        self.home_runs_per_9 = pitching_stats.get('homeRunsPer9', None)
        self.inherited_runners = pitching_stats.get('inheritedRunners', None)
        self.inherited_runners_scored = pitching_stats.get('inheritedRunnersScored', None)
        self.catchers_interference = pitching_stats.get('catchersInterference', None)
        self.sac_bunts = pitching_stats.get('sacBunts', None)
        self.sac_flies = pitching_stats.get('sacFlies', None)
        self.passed_balls = pitching_stats.get('passedBalls', None)
        self.pop_outs = pitching_stats.get('popOuts', None)
        self.line_outs = pitching_stats.get('lineOuts', None)
        # no children


class FieldingStats:
    def __init__(self, fielding_stats):
        self.caught_stealing = fielding_stats.get('caughtStealing', None)
        self.stolen_bases = fielding_stats.get('stolenBases', None)
        self.stolen_base_percentage = fielding_stats.get('stolenBasePercentage', None)
        self.assists = fielding_stats.get('assists', None)
        self.put_outs = fielding_stats.get('putOuts', None)
        self.errors = fielding_stats.get('errors', None)
        self.chances = fielding_stats.get('chances', None)
        self.passed_balls = fielding_stats.get('passedBalls', None)
        self.pickoffs = fielding_stats.get('pickoffs', None)


class Decisions:
    def __init__(self, decision):
        self.winner = decision.get('winner', None)
        self.loser = decision.get('loser', None)
        self.save = decision.get('save', None)
        self._children()

    def _children(self):
        self.winner = Player(self.winner)
        self.loser = Player(self.loser)

        if self.save is not None:
            self.save = Player(self.save)


def _convert_zulu_to_local(zulu_time_str) -> Tuple[int, int]:
    if zulu_time_str is None:
        return None

    zulu_time = datetime.strptime(zulu_time_str, '%Y-%m-%dT%H:%M:%SZ')
    zulu_time = pytz.utc.localize(zulu_time)

    local_timezone = datetime.now(timezone.utc).astimezone().tzinfo
    local_time = zulu_time.astimezone(local_timezone)

    t = local_time.strftime('%I:%M')

    if t[0] == str('0'):
        t = f' {t[1:]}'

    t = f'{t[0:2]} {t[3:]}'

    return (int(t[0:2]), int(t[3:]))


def _get_division(code: str) -> Union[str, None]: # pylint: disable=R0911
    if code in ('NYY', 'BOS', 'TB', 'BAL', 'TOR'):
        return 'AL East'
    if code in ('CWS', 'CLE', 'DET', 'KC', 'MIN'):
        return 'AL Central'
    if code in ('HOU', 'OAK', 'SEA', 'LAA', 'TEX'):
        return 'AL West'
    if code in ('ATL', 'MIA', 'NYM', 'PHI', 'WSH'):
        return 'NL East'
    if code in ('CHC', 'CIN', 'MIL', 'PIT', 'STL'):
        return 'NL Central'
    if code in ('ARI', 'COL', 'LAD', 'SD', 'SF'):
        return 'NL West'
    return None


def get_games() -> List[Game]:
    gamepks = get_daily_gamepks()
    games = []

    for pk in tqdm(gamepks):
        data = statsapi.get('game', {'gamePk': pk})
        games.append(Game(data))

    return games


def _get_utc_time(delay_seconds: int = 0):
    """
    returns the utc time in YYYMMDD-HHMMSS in 24 hour time

    Used for statsapi.get() functions that use time parameter
    'delay_seconds' can also be type float as well

    Args:
        delay_seconds (int, optional): Seconds behind present you want
        the output to be. Defaults to 0

    Raises:
        TypeError: If 'delay_seconds' is type str

    Returns:
        str: The UTC time in the 'YYYYMMDD-HHMMSS' format
    """
    # Get the current time in UTC
    utc_time = datetime.utcnow()

    # Subtract the delta
    utc_time = utc_time - timedelta(seconds=delay_seconds)

    # Format the time
    formatted_time = utc_time.strftime('%Y%m%d_%H%M%S')

    return formatted_time

def _get_utc_time_from_zulu(zulu_time_str):
    # Parse the time string with a timezone offset
    utc_time = datetime.fromisoformat(zulu_time_str.replace('Z', '+00:00'))

    # Convert to UTC (Zulu time)
    utc_time = utc_time.astimezone(tz.UTC)

    # Return the formatted UTC time in the desired format
    return utc_time.strftime('%Y%m%d_%H%M%S')


if __name__ == "__main__":
    game = Game.get_game_from_pk(gamepk = 717200, delay_seconds = 0)
