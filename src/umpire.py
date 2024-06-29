"""
Module holds the umpire class which is responsible for calculating
and holding information for missed calls in a MLB game. Trying to
reverse engineer the results from Ump Scorecards.

Classes:
    Umpire: Represents missed calls in a MLB game. Has the ability
        to calculate and find missed calls in the game

Example:

umpire = Umpire(gamePk = 717404)
umpire.calculate(print_missed_calls = True)

#or

num_miss, favor, missed_list = Umpire.find_missed_calls(gamePk = 717404,
                                            print_missed_calls = True)
"""

import csv
import os
from typing import List, Tuple
import random
import math
from src.game import Game, AllPlays, PlayEvents
from src.runners import Runners
from src.statsapi_plus import get_game_dict
from src.statsapi_plus import get_red288_dataframe

# center of ball needs to be .6870488261 hawkeye margin of errors away
# from the edge of the strike zone for the 90% rule to apply
# accoding to math

# Margin of Error for Hawkeye pitch tracking system.
# around 0.625"-0.700" based off tests
HAWKEYE_MARGIN_OF_ERROR_INCH = 0.690
HAWKEYE_MARGIN_OF_ERROR_FEET = HAWKEYE_MARGIN_OF_ERROR_INCH/12

# max distance a ball can be from strike zone edge before umpire
# call becomes incorrect. between 0.325 and 0.505 based of tests
BUFFER_INCH = .325
BUFFER_FEET = BUFFER_INCH / 12

class MissedCalls():
    def __init__(self, i: int, at_bat: AllPlays, pitch: PlayEvents, runners: Runners, home_favor):
        self._at_bat = at_bat
        self._pitch = pitch

        self.i = i
        self.pitcher = at_bat.matchup.pitcher.fullName
        self.batter = at_bat.matchup.batter.fullName
        self.inning = at_bat.about.inning
        self.half_inning = at_bat.about.halfInning.capitalize()

        self.balls = pitch.count.balls
        self.strikes = pitch.count.strikes
        self.outs = pitch.count.outs

        self.code = pitch.details.code

        self.zone = pitch.pitchData.zone
        self.px = pitch.pitchData.coordinates.pX
        self.pz = pitch.pitchData.coordinates.pZ
        self.px_min = pitch.pitchData.coordinates.PX_MIN
        self.px_max = pitch.pitchData.coordinates.PX_MAX
        self.pz_min = pitch.pitchData.coordinates.pZ_min
        self.pz_max = pitch.pitchData.coordinates.pZ_max
        self.sz_top = pitch.pitchData.coordinates.sZ_top
        self.sz_bot = pitch.pitchData.coordinates.sZ_bot

        self.runners = runners
        self.home_favor = home_favor

    def print_pitch(self):
        to_print_str = ''

        to_print_str += f'{self.i + 1}: {self.half_inning} {self.inning}\n'
        to_print_str += f'{self.pitcher} to {self.batter}\n'

        if self.outs == 1:
            to_print_str += f'{self.outs} out, '
        else:
            to_print_str += f'{self.outs} outs, '

        to_print_str += f'{str(self.runners)}\n'

        if self.code:
            to_print_str += f'{self.balls}-{self.strikes-1}, ball called strike\n'
        elif self.code:
            to_print_str += f'{self.balls-1}-{self.strikes}, strike called ball\n'

        to_print_str += f'px: {self.px:.5f} | pz: {self.pz:.5f}\n'
        to_print_str += f'left: {self.px_min:.5f} | right: {self.px_max:.5f}\n'
        to_print_str += f'top: {self.pz_max:.5f} | bottom: {self.pz_min:.5f}\n'

        to_print_str += f'Home Favor: {self.home_favor:4.2f}\n'

        print(to_print_str)

class Umpire():
    """
    Class that represents missed calls made by the umpire in a game

    Arguments:
        game: Game: The Game class that represents the given game. Takes
            priority over gamePk argument. Defaults to None
        gamePk: int: The gamePk number for the given game. The Game class
            will be automatically generated if game argument is not
            provided

    Attributes:
        gamePk (int): gamePk for given game
        game (Game): Game class for the given game. Automatically
            generated if gamePk argument is provided
        num_missed_calls (int): The number of missed calls in the game
        home_favor (float): The number of runs the home team were
            favored/gained from missed calls
        missed_calls (List[PlayEvents]): List of pitches that were
            called wrong throughout the game

    Raises:
        ValueError: If game and gamePk arguments are not provided in
            instance class initialized
    """
    hmoe = HAWKEYE_MARGIN_OF_ERROR_FEET
    red288 = get_red288_dataframe()

    def __init__(self, game: Game = None, gamepk: int = None,
                 delay_seconds: int = 0, method: str = None):

        self.delay_seconds: int = round(delay_seconds)

        if game is not None:
            self.game = game
        elif gamepk is not None:
            self.game = Game.get_game_from_pk(gamepk=gamepk,
                                              delay_seconds=self.delay_seconds)
        else:
            raise ValueError('gamePk and game arguments not provided')

        self.gamepk = self.game.gamepk
        self.num_missed_calls = 0
        self.missed_calls: List[MissedCalls] = []
        self.home_favor = 0
        self.method: str = method
        self._runners = Runners()

    def calculate_game(self, method: str = None) -> Tuple[int, float, List[PlayEvents]]:
        if method is not None:
            self.method = method

        for at_bat in self.game.liveData.plays.allPlays:
            self._runners.new_at_bat(at_bat)
            isTopInning = at_bat.about.isTopInning

            at_bat_last_pitch = len(at_bat.playEvents) - 1

            for pitch in at_bat.playEvents:
                if pitch.index != at_bat_last_pitch:
                    # check for steals
                    # might not be accurate when running live?
                    self._runners.process_runner_movement(at_bat.runners, pitch.index)

                if pitch.isPitch is True:
                    self._process_pitch(at_bat, pitch, isTopInning)

            self._runners.end_at_bat(at_bat)

    def _process_pitch(self, at_bat: AllPlays, pitch: PlayEvents, isTopInning: bool):
        runners_int = int(self._runners)
        is_first_base = bool(runners_int & 1)
        is_second_base = bool(runners_int & 2)
        is_third_base = bool(runners_int & 4)

        home_delta =  Umpire.delta_favor_single_pitch(pitch, isTopInning, is_first_base,
                                               is_second_base, is_third_base, self.method)

        if home_delta != 0:
            self.num_missed_calls += 1
            self.home_favor += home_delta
            self.missed_calls.append(MissedCalls(len(self.missed_calls), at_bat, pitch,
                                     self._runners, home_delta))

    def print_missed_calls(self):
        for call in self.missed_calls:
            call.print_pitch()

    def __int__(self):
        if self.num_missed_calls != len(self.missed_calls):
            raise ValueError('num_missed_calls and missed_calls do not match')
        return self.num_missed_calls

    def __float__(self):
        return self.home_favor

    def __str__(self):
        return f'{self.__repr__()}'

    def __repr__(self):
        if self.home_favor < 0:
            away_team = self.game.gameData.teams.away.abbreviation
            return f'+{-self.home_favor:.2f} {away_team}'
        home_team = self.game.gameData.teams.home.abbreviation
        return f'+{self.home_favor:.2f} {home_team}'

    @classmethod
    def _missed_pitch_details(cls, at_bat: AllPlays, runners: Runners,
                              pitch: PlayEvents, home_delta: float, i: int
                              ) -> str:
        """Helper method to find_missed_calls"""
        to_print_str = ''

        half_inn = at_bat.about.halfInning.capitalize()
        inning = at_bat.about.inning
        pitcher_name = at_bat.matchup.pitcher.fullName
        batter_name = at_bat.matchup.batter.fullName

        to_print_str += f'{i}: {half_inn} {inning}\n'
        to_print_str += f'{pitcher_name} to {batter_name}\n'

        if pitch.count.outs == 1:
            to_print_str += f'{pitch.count.outs} out, '
        else:
            to_print_str += f'{pitch.count.outs} outs, '

        to_print_str += f'{str(runners)}\n'

        balls = pitch.count.balls
        strikes = pitch.count.strikes

        if pitch.details.code == 'C':
            to_print_str += f'{balls}-{strikes-1}, ball called strike\n'
        elif pitch.details.code == 'B':
            to_print_str += f'{balls-1}-{strikes}, strike called ball\n'

        to_print_str += f'Zone: {pitch.pitchData.zone}\n'

        to_print_str += (f'pX = {pitch.pitchData.coordinates.pX:.5f} | '
                        f'pZ = {pitch.pitchData.coordinates.pZ:.5f}\n')

        to_print_str += (f'left: {pitch.pitchData.coordinates.PX_MIN:.5f} | '
                         f'right: {pitch.pitchData.coordinates.PX_MAX:.5f}\n')

        to_print_str += (f'bot = {pitch.pitchData.coordinates.pZ_bot:.5f} | '
                        f'top = {pitch.pitchData.coordinates.pZ_top:.5f}\n')

        to_print_str += f'Home Favor: {home_delta:4.2f}\n'

        return to_print_str

    @classmethod
    def delta_favor_single_pitch(cls, pitch: PlayEvents, isTopInning: bool,
                    is_first_base: bool, is_second_base: bool,
                    is_third_base: bool, method: str = None):
        """
        Calculates if a umpire made a bad call by either calling a pitch
        out of the zone a strike or a pitch in the zone a ball. There
        are three different methods that can be used based on the users
        choice. If the umpire did miss a call the function returns the
        amount of runs they effectively game the home team. A number
        greater than 0 means that they helped the home team while a
        number less than 0 means they helped the away team.

        Option 1: method = 'zone':
            The zone number is a single digit (1-9) if the pitch is a
            strike and a two digit number (11-14) if the pitch is a
            ball. MLB calculates the zone number automatically reducing
            the amount of work this function needs. Unfortunately most
            places that calculate umpire missed calls use some sort of
            buffer zone that allows for a pitch to miss by some amount
            while still giving the umpire the correct call
        Option 2: method = 'monte':
            The Hawkeye tracking system is not perfect and can miss a
            pitches real location by up to a quarter of an inch. This
            method calculates 500 potential pitch locations that the
            real pitch location could have been. For a pitch to be a
            missed call one of the two scenarios must be true:
                1. Called ball but >90% of simulated pitches were balls
                2. Called strike but >90% of simulated pitches were strikes

            This is what UmpScorecards claims they use:
            https://umpscorecards.com/explainers/accuracy
        Option 3: method = 'buffer':
            Most places that calculate missed calls made by umpires
            define a grace area that a pitch can land on and the correct
            call be made. That is what this method uses. If a pitch is
            within a certain distance from the edges of the strike zone,
            it returns 0 because that pitch can be called a ball or
            strike and still be correct. If a pitch falls outside the
            grace area, the homefavor will be calculated off the zone
            number due to its speed

        Args:
            pitch (PlayEvents): The pitch data from the game.PlayEvents
                class. The PlayEvents class holds all the pitch data
            isTopInning (bool): A boolean that represents if its the
                top inning. Flips the sign of the result to adjust for
                top/bottom of inning
            is_first_base (bool): Is there a runner on first
            is_second_base (bool): Is there a runner on second
            is_third_base (bool): Is there a runner on third
            method (str, optional): _description_. Defaults to None.

        Raises:
            TypeError: If isTopInning argument is not type bool

        Returns:
            float: The amount of runs the umpire gave for  pitch. 0 if
                pitch is swung or correct call was made.
        """

        if isinstance(isTopInning, bool) is False:
            raise TypeError('isTopInning should be type bool')

        if pitch.pitchData is None:
            return 0

        balls = pitch.count.balls
        strikes = pitch.count.strikes
        outs = pitch.count.outs

        if pitch.details.code not in ('C', 'B'):
            return 0

        if method == 'zone':
            correct = Umpire._is_correct_call_zone_num(pitch)
        if method == 'monte':
            if Umpire._check_valid_pitch(pitch) is False:
                return 0
            correct = Umpire._is_correct_call_monte_carlo(pitch)
        if method == 'buffer':
            if Umpire._check_valid_pitch(pitch) is False:
                return 0
            correct = Umpire._is_correct_call_buffer_zone(pitch)

        if correct is True:
            return 0


        if pitch.details.code == 'C':
            # Ball called Strike
            state = ((Umpire.red288['balls'] == balls) &
                    (Umpire.red288['strikes'] == strikes - 1) &
                    (Umpire.red288['outs'] == outs) &
                    (Umpire.red288['is_first_base'] == is_first_base) &
                    (Umpire.red288['is_second_base'] == is_second_base) &
                    (Umpire.red288['is_third_base'] == is_third_base))

            home_favor = Umpire.red288[state]['run_value'].iloc[0]
        if pitch.details.code == 'B':
            # Strike called Ball
            state = ((Umpire.red288['balls'] == balls - 1) &
                (Umpire.red288['strikes'] == strikes) &
                (Umpire.red288['outs'] == outs) &
                (Umpire.red288['is_first_base'] == is_first_base) &
                (Umpire.red288['is_second_base'] == is_second_base) &
                (Umpire.red288['is_third_base'] == is_third_base))

            home_favor = -1 * Umpire.red288[state]['run_value'].iloc[0]

        if isTopInning is True:
            return home_favor
        return -1 * home_favor

    @classmethod
    def _check_valid_pitch(cls, pitch):
        if pitch.pitchData is None:
            return False
        if pitch.pitchData.coordinates.is_valid() is False:
            return False
        return True

    @classmethod
    def _is_correct_call_zone_num(cls, pitch: PlayEvents) -> bool:
        """Helper method to delta_favor_zone"""
        if pitch.details.code == 'C' and pitch.pitchData.zone > 10:
            return False
        if pitch.details.code == 'B' and 1 <= pitch.pitchData.zone <= 9:
            return False
        return True

    @classmethod
    def _is_correct_call_monte_carlo(cls, pitch: PlayEvents) -> bool:
        """Helper method to delta_favor_zone"""
        strike = 0
        ball = 0

        pX_left = pitch.pitchData.coordinates.PX_MIN
        pX_right = pitch.pitchData.coordinates.PX_MAX
        pZ_top = pitch.pitchData.coordinates.pZ_max
        pZ_bot = pitch.pitchData.coordinates.pZ_min

        for _ in range(1, 501):
            rand_x, rand_z = Umpire._generage_random_pitch_location(pitch)

            if pX_left <= rand_x <= pX_right and pZ_bot <= rand_z <= pZ_top:
                strike += 1
            else:
                ball += 1

        total = ball + strike

        if pitch.details.code == 'B' and ((strike / total) > 0.90):
            return False
        if pitch.details.code =='C' and ((ball / total) > 0.90):
            return False
        return True

    @classmethod
    def _is_correct_call_buffer_zone(cls, pitch: PlayEvents) -> bool:
        buf = BUFFER_FEET # buffer in feet but short

        pX = pitch.pitchData.coordinates.pX
        pZ = pitch.pitchData.coordinates.pZ

        pZ_top = pitch.pitchData.coordinates.pZ_top
        pZ_bot = pitch.pitchData.coordinates.pZ_bot

        pX_left = pitch.pitchData.coordinates.PX_MIN
        pX_right = pitch.pitchData.coordinates.PX_MAX

        # left zone
        if (((pX_left - buf) <= pX <= (pX_left + buf)) and
            ((pZ_bot - buf) <= pZ <= (pZ_top + buf))):
            return True

        # right zone
        if (((pX_right - buf) <= pX <= (pX_right + buf)) and
            ((pZ_bot - buf) <= pZ <= (pZ_top + buf))):
            return True

        # top zone
        if (((pZ_top - buf) <= pZ <= (pZ_top + buf)) and
            ((pX_left - buf) <= pX <= (pX_right + buf))):
            return True

        # bottom zone
        if (((pZ_bot - buf) <= pZ <= (pZ_bot + buf)) and
            (pX_left - buf) <= pX <= (pX_right + buf)):
            return True

        return False

    @classmethod
    def _generage_random_pitch_location(cls, pitch: PlayEvents
                                        ) -> Tuple[float, float]:
        """Helper method to delta_favor_zone"""

        pX = pitch.pitchData.coordinates.pX
        pZ = pitch.pitchData.coordinates.pZ

        delta_radius = random.uniform(-cls.hmoe, cls.hmoe)
        angle = random.uniform(0, 360)
        angle = math.radians(angle)

        dx = delta_radius * math.cos(angle)
        dz = delta_radius * math.sin(angle)

        rand_x = pX + dx
        rand_z = pZ + dz

        return (rand_x, rand_z)

    @classmethod
    def _check_class_methods(cls, runners: Runners, runners_int: int, isTopInning: bool) -> int:
        if runners is None and runners_int is None:
            raise ValueError('runners and runners_int were not provided')
        if isinstance(runners_int, int) is False and runners_int is not None:
            raise TypeError('runners_int should be type int')
        if isinstance(isTopInning, bool) is False:
            raise TypeError('isTopInning should be type bool')

        if runners is not None:
            return int(runners)
        return runners_int

def sv_top_bot(gamePk: int):
    """
    Used to print top and bottom of strike zone so I can compare them to
    Baseball Savant since I think they might not match

    Args:
        gamePk (int): gamePk for the given game
    """
    game = get_game_dict(gamePk)
    game = Game(game)

    current_dir = os.path.dirname(os.path.realpath(__file__))
    csv_path = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(csv_path, 'sv_top_bot.csv')

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
        field_names = ['speed', 'pX', 'pZ', 'sZ_top', 'sZ_bot', 'zone']

        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()

        for at_bat in game.liveData.plays.allPlays:
            for pitch in at_bat.playEvents:
                if pitch.isPitch is True:
                    speed = pitch.pitchData.startSpeed
                    zone = pitch.pitchData.zone

                    pX = f'{pitch.pitchData.coordinates.pX:.2f}'
                    pZ = f'{pitch.pitchData.coordinates.pZ:.2f}'

                    sZ_top = f'{pitch.pitchData.coordinates.sZ_top:.2f}'
                    sZ_bot = f'{pitch.pitchData.coordinates.sZ_bot:.2f}'

                    writer.writerow({'speed': speed,
                                    'pX': pX,
                                    'pZ': pZ,
                                    'sZ_top': sZ_top,
                                    'sZ_bot': sZ_bot,
                                    'zone': zone})

if __name__ == '__main__':
    sv_top_bot(716997)
