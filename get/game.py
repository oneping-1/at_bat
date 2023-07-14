import datetime
import pytz
from typing import List, Tuple
from .statsapi_plus import get_daily_gamePks, get_run_expectency_numpy
from tqdm import tqdm
import statsapi
import random
import math

margin_of_error = .75/12 # Margin of Error of hawkeye system (inches)

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
        self.temp = weather.get('temp', None)
        self.wind = weather.get('wind', None)
        # no children

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

class PrimaryDatacaster:
    def __init__(self, primaryDatacaster):
        self.id = primaryDatacaster['id']
        self.fullName = primaryDatacaster['fullName']
        self.link = primaryDatacaster['link']
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
        self._test = plays
        self.allPlays: List[AllPlays] = [AllPlays(play) for play in plays['allPlays']]
        self.currentPlay = plays.get('currentPlay', None)
        
class AllPlays:
    """
    Holds data for each at bat
    """
    def __init__(self, allPlays):
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
        self.startTime = about['startTime']
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
    """
    Holds data for each pitch in at bat
    """
    MOE = margin_of_error
    renp = get_run_expectency_numpy()

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
       
    def calculate_delta_home_favor_zone_num(self, runners: List[bool], isTopInning: bool, moe: float = 0.083) -> float:
        home_delta = 0

        correct = True

        b = self.count.balls
        s = self.count.strikes
        o = self.count.outs

        r = self._get_runners_int(runners)

        if self.details.code == 'C' or self.details.code == 'B':
            correct = self._is_correct_call_zone_num()

        if correct is True:
            return 0
        elif self.details.code == 'C':
            # Ball called Strike
            home_delta += PlayEvents.renp[b+1][s-1][o][r] - PlayEvents.renp[b][s][o][r]
            ...
        elif self.details.code == 'B':
            # Strike called Ball
            home_delta += PlayEvents.renp[b-1][s+1][o][r] - PlayEvents.renp[b][s][o][r]
            ...

        if isTopInning is True:
            return home_delta
        return -home_delta

    def calculate_delta_home_favor_monte_carlo(self, runners: List[bool], isTopInning: bool, moe: float = 0.083) -> float:
        home_delta = 0

        correct = True

        b = self.count.balls
        s = self.count.strikes
        o = self.count.outs

        r = self._get_runners_int(runners)

        if self.details.code == 'C' or self.details.code == 'B':
            correct = self._is_correct_call_monte_carlo()

        if correct is True:
            return 0
        elif self.details.code == 'C':
            # Ball called Strike
            home_delta += PlayEvents.renp[b+1][s-1][o][r] - PlayEvents.renp[b][s][o][r]
            ...
        elif self.details.code == 'B':
            # Strike called Ball
            home_delta += PlayEvents.renp[b-1][s+1][o][r] - PlayEvents.renp[b][s][o][r]
            ...

        if isTopInning is True:
            return home_delta
        return -home_delta

    def _is_correct_call_zone_num(self) -> bool:        
        if self.details.code == 'C' and self.pitchData.zone > 10:
            return False
        elif self.details.code == 'B' and self.pitchData.zone >= 1 and self.pitchData.zone <= 9:
            return False
        else:
            return True
        
    def _is_correct_call_monte_carlo(self) -> bool:
        strike = 0
        ball = 0

        pz_left = -0.83
        pz_right = 0.83
        pZ_top = self.pitchData.coordinates.pZ_top
        pZ_bot = self.pitchData.coordinates.pZ_bot

        for _ in range(1, 501):
            rand_x, rand_z = self._generage_random_pitch_location()

            if (rand_x >= pz_left) and (rand_x <= pz_right) and (rand_z >= pZ_bot) and (rand_z <= pZ_top):
                strike += 1
            else:
                ball += 1
        
        total = ball + strike

        if self.details.code == 'B' and ((strike / total) >= 0.90):
            return False
        elif self.details.code =='C' and ((ball / total) >= 0.90):
            return False
        else:
            return True

    def _generage_random_pitch_location(self) -> Tuple[float, float]:
            dr = random.uniform(-margin_of_error, margin_of_error)
            dt = random.uniform(0, 360)
            dt = math.radians(dt)

            dx = dr * math.cos(dt)
            dz = dr * math.sin(dt)

            rand_x = self.pitchData.coordinates.pX + dx
            rand_z = self.pitchData.coordinates.pZ + dz

            return (rand_x, rand_z)

    @classmethod
    def _get_runners_int(cls, runners) -> int:
        r = 0

        if runners[0] is True:
            r += 1
        if runners[1] is True:
            r += 2
        if runners[2] is True:
            r += 4

        return r

    def pitch_in_the_zone_str(self, moe:float=0.083) -> str:
        s = ''
        
        if self.pitchData.zone >= 1 and self.pitchData.zone <= 9:
            s += 'In Zone'
        elif self.pitchData.zone > 10:
            s += 'Out of Zone'

        if (self.pitchData.coordinates.pZ >= (self.pitchData.coordinates.pZ_top - moe)) and (self.pitchData.coordinates.pZ >= (self.pitchData.coordinates.pZ_top + moe)) and (self.pitchData.coordinates.pX >= (-.83 - moe)) and (self.pitchData.coordinates.pX <= (.83 + moe)):
            s += ' (moe)'
        elif (self.pitchData.coordinates.pZ >= (self.pitchData.coordinates.pZ_bot - moe)) and (self.pitchData.coordinates.pZ >= (self.pitchData.coordinates.pZ_bot + moe)) and (self.pitchData.coordinates.pX >= (-.83 - moe)) and (self.pitchData.coordinates.pX <= (.83 + moe)):
            s += ' (moe)'
        elif (self.pitchData.coordinates.pX >= (-.83 - moe)) and (self.pitchData.coordinates.pX <= (-.83 + moe)) and (self.pitchData.coordinates.pZ >= self.pitchData.coordinates.pZ_bot) and (self.pitchData.coordinates.pZ <= self.pitchData.coordinates.pZ_top):
            s += ' (moe)'
        elif (self.pitchData.coordinates.pX >= (.83 - moe)) and (self.pitchData.coordinates.pX <= (.83 + moe)) and (self.pitchData.coordinates.pZ >= self.pitchData.coordinates.pZ_bot) and (self.pitchData.coordinates.pZ <= self.pitchData.coordinates.pZ_top):
            s += ' (moe)'

        return s

    def __eq__(self, other):
        if other is None:
            return False
        elif self._playEvents == other._playEvents:
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
    def __init__(self, type):
        self.code = type.get('code', None)
        self.description = type['description']
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
        self.typeConfindence = (pitchData.get('typeConfidence', None))
        self.plateTime = pitchData.get('plateTime', None)
        self.extension = (pitchData.get('extension', None))

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

class PitchCoordinates:
    def __init__(self, coor, sz_top, sz_bot):

        self.sZ_top = sz_top
        self.sZ_bot = sz_bot

        # Location of Center of Pitch for Ball/Strike
        self.pZ_top = self.sZ_top + 0.12
        self.pZ_bot = self.sZ_bot - 0.12

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

        # no children

    def is_correct_call(self, call_code:str, moe:float=0.083) -> bool:
            if call_code == 'C' or call_code == 'B' or call_code is None:
                raise ValueError('call_code not correct')
            
            pX_left = -0.83
            pX_right = 0.83

            # Could probably check if pitch is within moe and return true without checking call
            if call_code == 'C' and (self.pX >= (pX_left - moe)) and (self.pX <= (pX_right + moe)) and (self.pZ >= (self.pZ_bot - moe)) and (self.pZ <= (self.pZ_top + moe)):
                return True
            elif call_code == 'B' and ((self.pX <= (pX_left + moe)) or (self.pX >= (pX_right - moe)) or (self.pZ <= (self.pZ_bot + moe)) or (self.pZ >= (self.pZ_top - moe))):
                return True
            else:
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
        self.link = player['link']
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

def _get_delayed_timecode(delay_seconds):
    now = datetime.datetime.now()
    delay = datetime.timedelta(seconds=delay_seconds)

    new_time = now - delay
    return new_time.strftime('%m%d%Y_%H%M%S')

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
    gamePks = get_daily_gamePks()
    games = []

    for Pk in tqdm(gamePks):
        data = statsapi.get('game', {'gamePk': Pk})
        games.append(Game(data))

    return games

if __name__ == "__main__":
    print(_get_delayed_timecode(5))