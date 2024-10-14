import os
from typing import List
import csv
import tqdm
from at_bat.game import Game
from at_bat.runners import Runners

current_dir = os.path.dirname(os.path.abspath(__file__))
gamepk_csv_file_path = os.path.join(current_dir, 'gamepks.csv')
pitch_csv_file_path = os.path.join(current_dir, 'pitch.csv')

field_names = [ 'gamepk',
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
                'breaks_angle',
                'breaks_length',
                'breaks_y',
                'break_vertical',
                'break_vertical_induced',
                'break_horizontal',
                'spin_rate',
                'spin_direction']

class GameCSVCreator:
    def __init__(self, gamepk: int):
        self.gamepk = gamepk
        self.game = Game.get_game_from_pk(gamepk)
        self.runners: Runners = Runners()
        self.away_score = 0
        self.home_score = 0

        self.inning: int = None
        self.is_top_inning: bool = None
        self.last_is_top_inning: bool = None
        self.runs_at_start: int = 0 # runs at start of half inning
        self.runs_to_start: int = 0 # runs since the start of the half inning
        self.total_half_inning_runs: int = 0 # total runs in the half inning

        self.dict_game = {}
        self.dict_at_bat = {}
        self.dict_pitch = {}
        self.game_data: List[dict] = []

        self.dict_game['gamepk'] = self.gamepk

        # game.gameData
        self.dict_game['game_time'] = self.game.gameData.datetime.dateTime
        self.dict_game['stadium'] = self.game.gameData.venue.name
        self.dict_game['time_zone'] = self.game.gameData.venue.timeZone.offset
        self.dict_game['field_type'] = self.game.gameData.venue.fieldInfo.turfType
        self.dict_game['roof_type'] = self.game.gameData.venue.fieldInfo.roofType
        self.dict_game['weather_sky'] = self.game.gameData.weather.condition
        self.dict_game['temperature'] = self.game.gameData.weather.temp
        self.dict_game['wind'] = self.game.gameData.weather.wind
        self.dict_game['attendance'] = self.game.gameData.gameInfo.attendance
        self.dict_game['game_duration'] = self.game.gameData.gameInfo.gameDurationMinutes
        self.dict_game['away_final_score'] = self.game.liveData.linescore.teams.away.runs
        self.dict_game['home_final_score'] = self.game.liveData.linescore.teams.home.runs
        self.dict_game['innings_final'] = self.game.liveData.linescore.currentInning

    def iterate_at_bats(self):
        for at_bat in self.game.liveData.plays.allPlays:
            # half inning total runs
            self.inning = at_bat.about.inning
            self.is_top_inning = at_bat.about.isTopInning

            self.runners.new_at_bat(at_bat)

            self.dict_at_bat = {}

            # runs to start/end of inning
            if self.is_top_inning:
                self.total_half_inning_runs = self.game.liveData.linescore.innings[self.inning - 1].away.runs
            else:
                self.total_half_inning_runs = self.game.liveData.linescore.innings[self.inning - 1].home.runs

            if self.total_half_inning_runs is None:
                # There was an error where the runs were not defined
                # for a half inning (2023-04-28 MIA vs CLE B9 I believe)
                self.total_half_inning_runs = 0

            self.dict_at_bat['total_half_inning_runs'] = self.total_half_inning_runs

            if self.last_is_top_inning != self.is_top_inning:
                self.last_is_top_inning = self.is_top_inning

                if self.is_top_inning:
                    self.runs_at_start = self.away_score
                else:
                    self.runs_at_start = self.home_score

            if self.is_top_inning:
                self.runs_to_start = self.away_score - self.runs_at_start
            else:
                self.runs_to_start = self.home_score - self.runs_at_start

            self.dict_at_bat['runs_to_start'] = self.runs_to_start
            self.dict_at_bat['runs_to_end'] = self.total_half_inning_runs - self.runs_to_start

            # atBat.about
            self.dict_at_bat['inning'] = at_bat.about.inning
            self.dict_at_bat['is_top_inning'] = at_bat.about.isTopInning
            self.dict_at_bat['away_score'] = self.away_score
            self.dict_at_bat['home_score'] = self.home_score

            # atBat.matchup
            self.dict_at_bat['batter'] = at_bat.matchup.batter.fullName
            self.dict_at_bat['bat_side'] = at_bat.matchup.batSide.description
            self.dict_at_bat['pitcher'] = at_bat.matchup.pitcher.fullName
            self.dict_at_bat['pitch_hand'] = at_bat.matchup.pitchHand.description

            self.iterate_pitches(at_bat)
            self.runners.end_at_bat(at_bat)

            self.away_score = at_bat.result.awayScore
            self.home_score = at_bat.result.homeScore


    def iterate_pitches(self, at_bat):
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
                self.runners.process_runner_movement(at_bat.runners, play_event.index)

            if play_event.isPitch:
                self.dict_pitch = {}
                # playEvent.details
                self.dict_pitch['pitch_result'] = play_event.details.description
                self.dict_pitch['pitch_result_code'] = play_event.details.code

                if play_event.details.type is not None:
                    self.dict_pitch['pitch_type_code'] = play_event.details.type.code
                    self.dict_pitch['pitch_type_description'] = play_event.details.type.description
                else:
                    self.dict_pitch['pitch_type_code'] = None
                    self.dict_pitch['pitch_type_description'] = None

                if balls == 4:
                    print(f'4 balls. {at_bat.matchup.pitcher.fullName} to {at_bat.matchup.batter.fullName} in game {self.gamepk}')
                if strikes == 3:
                    print(f'3 strikes. {at_bat.about.pitcher.fullName} to {at_bat.about.batter.fullName} in game {self.gamepk}')

                # playEvent.count
                self.dict_pitch['balls'] = balls
                self.dict_pitch['strikes'] = strikes
                self.dict_pitch['outs'] = play_event.count.outs
                self.dict_pitch['pitch_index'] = play_event.index

                # playEvent.pitchData
                self.dict_pitch['pitch_start_speed'] = play_event.pitchData.startSpeed
                self.dict_pitch['pitch_end_speed'] = play_event.pitchData.endSpeed
                self.dict_pitch['strike_zone_top'] = play_event.pitchData.coordinates.sZ_top
                self.dict_pitch['strike_zone_bottom'] = play_event.pitchData.coordinates.sZ_bot

                self.dict_pitch['zone'] = play_event.pitchData.zone
                self.dict_pitch['type_confidence'] = play_event.pitchData.typeConfidence
                self.dict_pitch['plate_time'] = play_event.pitchData.plateTime
                self.dict_pitch['extension'] = play_event.pitchData.extension

                # playEvent.pitchData.coordinates
                self.dict_pitch['px'] = play_event.pitchData.coordinates.pX
                self.dict_pitch['pz'] = play_event.pitchData.coordinates.pZ

                # playEvent.pitchData.breaks
                if play_event.pitchData.breaks:
                    self.dict_pitch['breaks_angle'] = play_event.pitchData.breaks.breakAngle
                    self.dict_pitch['breaks_length'] = play_event.pitchData.breaks.breakLength
                    self.dict_pitch['breaks_y'] = play_event.pitchData.breaks.breakY
                    self.dict_pitch['break_vertical'] = play_event.pitchData.breaks.breakVertical
                    self.dict_pitch['break_vertical_induced'] = play_event.pitchData.breaks.breakVerticalInduced
                    self.dict_pitch['break_horizontal'] = play_event.pitchData.breaks.breakHorizontal
                    self.dict_pitch['spin_rate'] = play_event.pitchData.breaks.spinRate
                    self.dict_pitch['spin_direction'] = play_event.pitchData.breaks.spinDirection
                else:
                    self.dict_pitch['breaks_angle'] = None
                    self.dict_pitch['breaks_length'] = None
                    self.dict_pitch['breaks_y'] = None
                    self.dict_pitch['break_vertical'] = None
                    self.dict_pitch['break_vertical_induced'] = None
                    self.dict_pitch['break_horizontal'] = None
                    self.dict_pitch['spin_rate'] = None
                    self.dict_pitch['spin_direction'] = None

                self.dict_game['pitch_time'] = play_event.startTime

                # runners
                self.dict_pitch['is_first_base'] = bool(self.runners.runners[0])
                self.dict_pitch['is_second_base'] = bool(self.runners.runners[1])
                self.dict_pitch['is_third_base'] = bool(self.runners.runners[2])

                if play_event.index == at_bat_last_pitch:
                    self.dict_pitch['at_bat_event'] = at_bat.result.event
                    self.dict_pitch['at_bat_event_type'] = at_bat.result.eventType
                    self.dict_pitch['at_bat_description'] = at_bat.result.description
                    self.dict_pitch['at_bat_rbi'] = at_bat.result.rbi

                if play_event.hitData is not None:
                    self.dict_pitch['batted_ball_launch_speed'] = play_event.hitData.launchSpeed
                    self.dict_pitch['batted_ball_launch_angle'] = play_event.hitData.launchAngle
                    self.dict_pitch['batted_ball_total_distance'] = play_event.hitData.totalDistance
                    self.dict_pitch['batted_ball_trajectory'] = play_event.hitData.trajectory
                    self.dict_pitch['batted_ball_hardness'] = play_event.hitData.hardness
                    self.dict_pitch['batted_ball_location'] = play_event.hitData.location
                    self.dict_pitch['batted_ball_coordinates_x'] = play_event.hitData.coordinates.coordX
                    self.dict_pitch['batted_ball_coordinates_y'] = play_event.hitData.coordinates.coordY

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
                combined_dict.update(self.dict_game)
                combined_dict.update(self.dict_at_bat)
                combined_dict.update(self.dict_pitch)
                self.game_data.append(combined_dict)

    def write_csv(self):
        with open(pitch_csv_file_path, 'a', newline='', encoding='UTF-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            for row in self.game_data:
                writer.writerow(row)

def start_csv():
    with open(pitch_csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

def read_gamepk_csv() -> List[int]:
    """
    Reads the gamepks from the gamepks.csv file and returns them as a
    list of integers

    Returns:
        List[int]: List of gamepks
    """
    gamepks: List[int] = []

    with open(gamepk_csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            gamepks.append(int(row[0]))

    return gamepks

def main():
    """
    Main function that creates a GameCSVCreator object for each gamepk
    """
    gamepks = read_gamepk_csv()
    # gamepks = [716373]
    start_csv()
    # gamepks = get_daily_gamepks('2024-05-01')
    for gamepk in tqdm.tqdm(gamepks):
        g = GameCSVCreator(gamepk)
        g.iterate_at_bats()
        g.write_csv()

if __name__ == '__main__':
    main()
