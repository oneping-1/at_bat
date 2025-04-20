import csv

from typing import List, Tuple
import pandas as pd

from at_bat.game import Game, AllPlays
from at_bat.runners import Runners
from at_bat.statsapi_plus import get_expected_values_dataframe
from at_bat.umpire2 import Umpire

umpire = Umpire()

xdf = get_expected_values_dataframe()
def batted_ball_expected_values(at_bat_event_type: str, exit_velo: float, launch_angle: int) -> Tuple[float, float]:
    """
    Returns expected batting average and expected slugging percentage
    based on a batted balls exit velocity and launch angle

    Args:
        at_bat_event_type (str): outcome of the at bat
        exit_velo (float): batted ball's exit velocity
        launch_angle (int): batted ball's launch angle

    Returns:
        Tuple[float, float]: xba, xslg
    """
    if at_bat_event_type is None:
        return (None, None)
    if at_bat_event_type in ('strikeout'):
        return (0, 0)
    if at_bat_event_type in ('walk', 'hit_by_pitch', 'catchers_inferf'):
        return (None, None)
    if (exit_velo is None) or (launch_angle is None):
        return (None, None)
    exit_velo = round(exit_velo, 1)
    launch_angle = round(launch_angle, 0)
    row = xdf.query('(exit_velocity == @exit_velo) & (launch_angle == @launch_angle)')
    xba = float(row['xba'].iloc[0])
    xslg = float(row['xslg'].iloc[0])
    return (xba, xslg)

class GameParser:
    field_names = [
            'gamepk',
            'game_time',
            'away_final_score',
            'home_final_score',
            'innings_final',
            'stadium',
            'time_zone',
            'field_type',
            'roof_type',
            'weather_sky',
            'temperature',
            'wind',
            'attendance',
            'game_duration',
            'inning',
            'is_top_inning',
            'runs_to_start', # runs to start of inning
            'runs_to_end', # runs to end of inning
            'total_half_inning_runs',
            'away_score',
            'home_score',
            'batter',
            'bat_side',
            'pitcher',
            'pitch_hand',
            'pitch_result',
            'pitch_result_code',
            'pitch_type_code',
            'pitch_type_description',
            'pitch_time',
            'at_bat_event',
            'at_bat_event_type',
            'at_bat_description',
            'at_bat_rbi',
            'batted_ball_launch_speed',
            'batted_ball_launch_angle',
            'batted_ball_total_distance',
            'batted_ball_trajectory',
            'batted_ball_hardness',
            'batted_ball_location',
            'batted_ball_coordinates_x',
            'batted_ball_coordinates_y',
            'batted_ball_xba',
            'batted_ball_xslg',
            'is_first_base',
            'is_second_base',
            'is_third_base',
            'balls',
            'strikes',
            'outs',
            'pitch_index',
            'pitch_start_speed',
            'pitch_end_speed',
            'strike_zone_top',
            'strike_zone_bottom',
            'zone',
            'type_confidence',
            'plate_time',
            'extension',
            'px',
            'pz',
            'sz_top',
            'sz_bot',
            'pz_min',
            'pz_max',
            'breaks_angle',
            'breaks_length',
            'breaks_y',
            'break_vertical',
            'break_vertical_induced',
            'break_horizontal',
            'spin_rate',
            'spin_direction'
        ]

    def __init__(self, gamepk: int):
        self.gamepk = gamepk
        self.game = Game.get_game_from_pk(gamepk)
        self._runners: Runners = Runners()
        self._away_score = 0
        self._home_score = 0

        self._inning: int = None
        self._is_top_inning: bool = None
        self._last_is_top_inning: bool = None
        self._runs_at_start: int = 0 # runs at start of half inning
        self._runs_to_start: int = 0 # runs since the start of the half inning
        self._total_half_inning_runs: int = 0 # total runs in the half inning

        self._dict_game = {}
        self._dict_at_bat = {}
        self._dict_pitch = {}
        self.game_data: List[dict] = []

        self._dict_game['gamepk'] = self.gamepk

        # game.gameData
        self._dict_game['game_time'] = self.game.gameData.datetime.dateTime
        self._dict_game['stadium'] = self.game.gameData.venue.name
        self._dict_game['time_zone'] = self.game.gameData.venue.timeZone.offset
        self._dict_game['field_type'] = self.game.gameData.venue.fieldInfo.turfType
        self._dict_game['roof_type'] = self.game.gameData.venue.fieldInfo.roofType
        self._dict_game['weather_sky'] = self.game.gameData.weather.condition
        self._dict_game['temperature'] = self.game.gameData.weather.temp
        self._dict_game['wind'] = self.game.gameData.weather.wind
        self._dict_game['attendance'] = self.game.gameData.gameInfo.attendance
        self._dict_game['game_duration'] = self.game.gameData.gameInfo.gameDurationMinutes
        self._dict_game['away_final_score'] = self.game.liveData.linescore.teams.away.runs
        self._dict_game['home_final_score'] = self.game.liveData.linescore.teams.home.runs
        self._dict_game['innings_final'] = self.game.liveData.linescore.currentInning

        self._iterate_at_bats()
        self.dataframe: pd.DataFrame = pd.DataFrame(self.game_data)

    def _iterate_at_bats(self):
        for at_bat in self.game.liveData.plays.allPlays:
            # half inning total runs
            self._inning = at_bat.about.inning

            # if self.inning >= 9:
            #     # ignore potential walk off scenarios that lead
            #     # to abbreviated innings
            #     return

            self._is_top_inning = at_bat.about.isTopInning

            self._runners.new_at_bat(at_bat)

            self._dict_at_bat = {}

            # runs to start/end of inning
            if self._is_top_inning:
                self._total_half_inning_runs = self.game.liveData.linescore.innings[self._inning - 1].away.runs
            else:
                self._total_half_inning_runs = self.game.liveData.linescore.innings[self._inning - 1].home.runs

            if self._total_half_inning_runs is None:
                # There was an error where the runs were not defined
                # for a half inning (2023-04-28 MIA vs CLE B9 I believe)
                self._total_half_inning_runs = 0

            self._dict_at_bat['total_half_inning_runs'] = self._total_half_inning_runs

            if self._last_is_top_inning != self._is_top_inning:
                self._last_is_top_inning = self._is_top_inning

                if self._is_top_inning:
                    self._runs_at_start = self._away_score
                else:
                    self._runs_at_start = self._home_score

            if self._is_top_inning:
                self._runs_to_start = self._away_score - self._runs_at_start
            else:
                self._runs_to_start = self._home_score - self._runs_at_start

            self._dict_at_bat['runs_to_start'] = self._runs_to_start
            self._dict_at_bat['runs_to_end'] = self._total_half_inning_runs - self._runs_to_start

            # atBat.about
            self._dict_at_bat['inning'] = at_bat.about.inning
            self._dict_at_bat['is_top_inning'] = at_bat.about.isTopInning
            self._dict_at_bat['away_score'] = self._away_score
            self._dict_at_bat['home_score'] = self._home_score

            # atBat.matchup
            self._dict_at_bat['batter'] = at_bat.matchup.batter.fullName
            self._dict_at_bat['bat_side'] = at_bat.matchup.bat_side.description
            self._dict_at_bat['pitcher'] = at_bat.matchup.pitcher.fullName
            self._dict_at_bat['pitch_hand'] = at_bat.matchup.pitch_hand.description

            self._iterate_pitches(at_bat)
            self._runners.end_at_bat(at_bat)

            self._away_score = at_bat.result.awayScore
            self._home_score = at_bat.result.homeScore

    def _iterate_pitches(self, at_bat: AllPlays):
        balls = 0
        strikes = 0

        if len(at_bat.playEvents) == 0:
            # No pitches thrown in the at bat
            # Santos to Olivares | 2023-09-05 | B9 (walkoff balk)
            return

        at_bat_last_pitch = at_bat.playEvents[-1].index

        for i, play_event in enumerate(at_bat.playEvents):

            if i != at_bat_last_pitch:
                # igonres the last pitch of the at bat
                # ball in play or what not
                # handled by
                self._runners.process_runner_movement(at_bat.runners, play_event.index)

            if play_event.is_pitch:
                self._dict_pitch = {}
                # playEvent.details
                self._dict_pitch['pitch_result'] = play_event.details.description
                self._dict_pitch['pitch_result_code'] = play_event.details.code

                if play_event.details.type is not None:
                    self._dict_pitch['pitch_type_code'] = play_event.details.type.code
                    self._dict_pitch['pitch_type_description'] = play_event.details.type.description
                else:
                    self._dict_pitch['pitch_type_code'] = None
                    self._dict_pitch['pitch_type_description'] = None

                if balls == 4:
                    print(f'4 balls. {at_bat.matchup.pitcher.fullName} to {at_bat.matchup.batter.fullName} in game {self.gamepk}')
                if strikes == 3:
                    print(f'3 strikes. {at_bat.about.pitcher.fullName} to {at_bat.about.batter.fullName} in game {self.gamepk}')

                # playEvent.count
                self._dict_pitch['balls'] = balls
                self._dict_pitch['strikes'] = strikes
                self._dict_pitch['outs'] = play_event.count.outs
                self._dict_pitch['pitch_index'] = play_event.index

                # playEvent.pitchData
                self._dict_pitch['pitch_start_speed'] = play_event.pitch_data.startSpeed
                self._dict_pitch['pitch_end_speed'] = play_event.pitch_data.endSpeed
                self._dict_pitch['strike_zone_top'] = play_event.pitch_data.coordinates.sZ_top
                self._dict_pitch['strike_zone_bottom'] = play_event.pitch_data.coordinates.sZ_bot

                self._dict_pitch['zone'] = play_event.pitch_data.zone
                self._dict_pitch['type_confidence'] = play_event.pitch_data.typeConfidence
                self._dict_pitch['plate_time'] = play_event.pitch_data.plateTime
                self._dict_pitch['extension'] = play_event.pitch_data.extension

                # playEvents.pitchData
                self._dict_pitch['sz_top'] = play_event.pitch_data.coordinates.sZ_top
                self._dict_pitch['sz_bot'] = play_event.pitch_data.coordinates.sZ_bot
                self._dict_pitch['pz_min'] = play_event.pitch_data.coordinates.pZ_min
                self._dict_pitch['pz_max'] = play_event.pitch_data.coordinates.pZ_max

                # playEvent.pitchData.coordinates
                self._dict_pitch['px'] = play_event.pitch_data.coordinates.pX
                self._dict_pitch['pz'] = play_event.pitch_data.coordinates.pZ

                # playEvent.pitchData.breaks
                if play_event.pitch_data.breaks:
                    self._dict_pitch['breaks_angle'] = play_event.pitch_data.breaks.breakAngle
                    self._dict_pitch['breaks_length'] = play_event.pitch_data.breaks.breakLength
                    self._dict_pitch['breaks_y'] = play_event.pitch_data.breaks.breakY
                    self._dict_pitch['break_vertical'] = play_event.pitch_data.breaks.breakVertical
                    self._dict_pitch['break_vertical_induced'] = play_event.pitch_data.breaks.breakVerticalInduced
                    self._dict_pitch['break_horizontal'] = play_event.pitch_data.breaks.breakHorizontal
                    self._dict_pitch['spin_rate'] = play_event.pitch_data.breaks.spinRate
                    self._dict_pitch['spin_direction'] = play_event.pitch_data.breaks.spinDirection
                else:
                    self._dict_pitch['breaks_angle'] = None
                    self._dict_pitch['breaks_length'] = None
                    self._dict_pitch['breaks_y'] = None
                    self._dict_pitch['break_vertical'] = None
                    self._dict_pitch['break_vertical_induced'] = None
                    self._dict_pitch['break_horizontal'] = None
                    self._dict_pitch['spin_rate'] = None
                    self._dict_pitch['spin_direction'] = None

                self._dict_game['pitch_time'] = play_event.start_time

                # runners
                self._dict_pitch['is_first_base'] = bool(self._runners.runners[0])
                self._dict_pitch['is_second_base'] = bool(self._runners.runners[1])
                self._dict_pitch['is_third_base'] = bool(self._runners.runners[2])

                at_bat_event_type = None
                if play_event.index == at_bat_last_pitch:
                    self._dict_pitch['at_bat_event'] = at_bat.result.event
                    at_bat_event_type = at_bat.result.eventType
                    self._dict_pitch['at_bat_event_type'] = at_bat_event_type
                    self._dict_pitch['at_bat_description'] = at_bat.result.description
                    self._dict_pitch['at_bat_rbi'] = at_bat.result.rbi

                ev = None
                la = None
                if play_event.hit_data is not None:
                    ev = play_event.hit_data.launchSpeed
                    la = play_event.hit_data.launchAngle
                    self._dict_pitch['batted_ball_launch_speed'] = ev
                    self._dict_pitch['batted_ball_launch_angle'] = la
                    self._dict_pitch['batted_ball_total_distance'] = play_event.hit_data.totalDistance
                    self._dict_pitch['batted_ball_trajectory'] = play_event.hit_data.trajectory
                    self._dict_pitch['batted_ball_hardness'] = play_event.hit_data.hardness
                    self._dict_pitch['batted_ball_location'] = play_event.hit_data.location
                    self._dict_pitch['batted_ball_coordinates_x'] = play_event.hit_data.coordinates.coordX
                    self._dict_pitch['batted_ball_coordinates_y'] = play_event.hit_data.coordinates.coordY

                umpire.from_game_parser(self._dict_at_bat, self._dict_pitch, self._runners)
                x = umpire.calculate_favors()
                run_favor, wp_favor = x
                self._dict_pitch['run_favor'] = run_favor
                self._dict_pitch['wp_favor'] = wp_favor

                xba, xslg = batted_ball_expected_values(at_bat_event_type, ev, la)
                self._dict_pitch['batted_ball_xba'] = xba
                self._dict_pitch['batted_ball_xslg'] = xslg

                # Placed after so the count recorded is before the pitch
                if play_event.details.isBall:
                    balls += 1

                if play_event.details.isStrike:
                    if play_event.details.code == 'F' and strikes == 2:
                        pass # Foul on 2 strikes, no change in count
                        # bunt foul ball on 2 strikes should be caught
                        # by the next at bat event
                    else:
                        strikes += 1

                combined_dict = {}
                combined_dict.update(self._dict_game)
                combined_dict.update(self._dict_at_bat)
                combined_dict.update(self._dict_pitch)
                self.game_data.append(combined_dict)

    def write_csv(self, file_path: str, write_header: bool = False):
        with open(file_path, 'a', newline='', encoding='UTF-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=GameParser.field_names)
            if write_header is True:
                writer.writeheader()
            for row in self.game_data:
                writer.writerow(row)

    def __str__(self):
        return self.dataframe.to_string()

if __name__ == '__main__':
    GAMEPK = 748542
    g = GameParser(GAMEPK)
    g = g.dataframe
    # print(g[~(pd.isna(g['at_bat_event_type']))][['at_bat_event_type' , 'batted_ball_xba']])
    print(g.loc[
        ((g['pitch_result_code'] == 'B') |
        (g['pitch_result_code'] == 'C')) &
        (g['run_favor'] > 0)
    ][['run_favor', 'wp_favor']])
