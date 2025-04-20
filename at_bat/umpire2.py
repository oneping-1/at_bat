from typing import List, Tuple
import math
import random

from at_bat.statsapi_plus import get_red288_dataframe, get_wpd351360_dataframe
from at_bat.runners import Runners

def _generate_monte_carlo_pitch_locations(num_pitches: int) -> List[Tuple[float, float]]:
    buffer = .5/12 # unit: inch
    random.seed(0)
    pitches: List[Tuple[float, float]] = []

    while True:
        dx = random.uniform(-buffer, buffer)
        dz = random.uniform(-buffer, buffer)

        if math.sqrt(dx**2 + dz**2) <= buffer:
            pitches.append((dx, dz))

        if len(pitches) >= num_pitches:
            return pitches
_monte_carlo_pitch_locations = _generate_monte_carlo_pitch_locations(500)
_red288 = get_red288_dataframe()
_wpd351360 = get_wpd351360_dataframe()

class Umpire:
    def __init__(self):
        self.pitch_result_code = None

        self.px = None
        self.pz = None

        self.sz_top = None
        self.sz_bot = None
        self.pz_top = None
        self.pz_bot = None

        self.balls = None
        self.strikes = None
        self.outs = None

        self.runners = None
        self.home_lead = None
        self.inning = None
        self.is_top_inning: bool = None

        self.method = None

        self.run_favor: float = None
        self.wp_favor: float = None

    def from_game_parser(self, at_bat: dict, pitch: dict, runners: Runners):
        self.pitch_result_code = pitch['pitch_result_code']

        self.px = pitch['px']
        self.pz = pitch['pz']

        self.sz_top = pitch['sz_top']
        self.sz_bot = pitch['sz_bot']
        self.pz_top = pitch['pz_max']
        self.pz_bot = pitch['pz_min']

        self.balls = pitch['balls']
        self.strikes = pitch['strikes']
        self.outs = pitch['outs']

        self.runners = int(runners)
        self.home_lead = at_bat['home_score'] - at_bat['away_score']
        self.inning = at_bat['inning']
        self.is_top_inning = at_bat['is_top_inning']

    def calculate_favors(self, method = None) -> Tuple[float, float]:
        if self.pitch_result_code not in ('B', 'C'):
            self.run_favor = None
            self.wp_favor = None
            return (None, None)

        if method is not None:
            self.method = method

        return self._calculate_monte_carlo()

    def _calculate_monte_carlo(self):
        balls = 0
        strikes = 0

        for dx, dz in _monte_carlo_pitch_locations:
            px = self.px + dx
            pz = self.pz + dz

            if (-.83 <= px <= .83) and (self.pz_bot <= pz <= self.pz_top):
                strikes += 1
            else:
                balls += 1

        total = balls + strikes
        if (self.pitch_result_code == 'B') and ((balls/total) >= .1):
            self.run_favor = 0
            self.wp_favor = 0
            return (0, 0)
        if (self.pitch_result_code == 'C') and ((strikes/total) >= .1):
            self.run_favor = 0
            self.wp_favor = 0
            return (0, 0)


        # if self.pitch_result_code == 'C':
        #     self.strikes -= 1
        # if self.pitch_result_code == 'B':
        #     self.balls -= 1

        self.inning = min(self.inning, 10)

        self.run_favor = _red288.loc[
            (_red288['balls'] == self.balls) &
            (_red288['strikes'] == self.strikes) &
            (_red288['outs'] == self.outs) &
            (_red288['is_first_base'] == bool(self.runners & 1)) &
            (_red288['is_second_base'] == bool(self.runners & 2)) &
            (_red288['is_third_base'] == bool(self.runners & 4))
        ]['run_value'].iloc[0]

        self.wp_favor = _wpd351360.loc[
            (_wpd351360['balls'] == self.balls) &
            (_wpd351360['strikes'] == self.strikes) &
            (_wpd351360['outs'] == self.outs) &
            (_wpd351360['is_first_base'] == bool(self.runners & 1)) &
            (_wpd351360['is_second_base'] == bool(self.runners & 2)) &
            (_wpd351360['is_third_base'] == bool(self.runners & 4)) &
            (_wpd351360['inning'] == self.inning) &
            (_wpd351360['is_top_inning'] == self.is_top_inning) &
            (_wpd351360['home_lead'] == self.home_lead)
        ]['wpa'].iloc[0]

        if self.pitch_result_code == 'B':
            self.run_favor *= -1
            self.wp_favor *= -1

        if self.is_top_inning is True:
            return (self.run_favor, self.wp_favor)

        self.run_favor *= -1
        return (self.run_favor, self.wp_favor)

if __name__ == '__main__':
    ump = Umpire()
    ump.calculate_favors()
