"""
This module contains the ScoreboardData class which is a simplified
version of the Game object which holds information that is displayed
on the scoreboard. This object is used to easaily access the data
needed to display the scoreboard and return changes in the data.

Raises:
    ValueError: If isTopInning is not a boolean
"""

import copy
from datetime import datetime, timedelta, timezone
import json
from typing import List
import numpy as np
import pandas as pd

from at_bat.statsapi_plus import get_re640_dataframe, get_wp780800_dataframe, get_expected_values_dataframe,find_division_from_abv
from at_bat.game import Game
from at_bat.game_parser import GameParser
from at_bat.runners import Runners
from at_bat.standings import Standings

re640 = get_re640_dataframe()
wp780800 = get_wp780800_dataframe()
expected_values = get_expected_values_dataframe()
division_from_abv = find_division_from_abv()


def dict_diff(dict1: dict, dict2: dict) -> dict:
    """Return the difference between two dictionaries

    Args:
        dict1 (dict): Dictionary 1
        dict2 (dict): Dictionary 2

    Returns:
        dict: The difference between the two dictionaries
    """
    diff = {}

    for key in dict1.keys() | dict2.keys():
        if dict1.get(key) != dict2.get(key):
            if isinstance(dict1.get(key), dict) and isinstance(dict2.get(key), dict):
                sub_diff = dict_diff(dict1.get(key), dict2.get(key))
                if sub_diff:
                    diff[key] = sub_diff
            else:
                diff[key] = dict2.get(key)

    return diff

def get_player_last_name(game: Game, player_id: int) -> str:
    """
    Return the last name of a player given their player_id

    Args:
        game (Game): The Game object
        player_id (int): The player_id

    Returns:
        str: The last name of the player
    """
    if player_id is None:
        return None

    player = game.gameData.players[f'ID{player_id}']
    return player['lastName']

class ScoreboardStandings:
    """
    Contains the standings data for any team based on their abbreviation.
    Seperate from the ScoreboardData object so that i can be called
    without the need for a gamepk.
    """
    def __init__(self, abv: str):
        self.abv = abv

        try:
            division = division_from_abv[abv]
        except KeyError:
            print(f'KeyError for {abv}')
            self.wins = 0
            self.losses = 0
            self.division_rank = 0
            self.games_back = 0
            self.streak = 'W0'
            return None

        league = division[0]
        division = division[1]

        # Spring Training
        # if league == 'A':
        #     standings = Standings.get_standings(league='AL')
        #     if division == 'E':
        #         standings = standings.central
        #     elif division == 'C':
        #         standings = standings.west
        #     elif division == 'W':
        #         standings = standings.east
        # else:
        #     standings = Standings.get_standings(league='NL')
        #     if division == 'E':
        #         standings = standings.west
        #     elif division == 'C':
        #         standings = standings.east
        #     elif division == 'W':
        #         standings = standings.central

        standings = Standings.get_standings(league=f'{league}L')
        if division == 'E':
            standings = standings.east
        elif division == 'C':
            standings = standings.central
        elif division == 'W':
            standings = standings.west

        for team in standings.team_records:
            if team.team.abv == abv:
                self.wins = team.wins
                self.losses = team.losses
                self.division_rank = team.division_rank
                self.games_back = team.games_back

                if team.streak is not None:
                    self.streak = team.streak.streakCode
                else:
                    self.streak = 'W0'

class Flags:
    """
    Contains the flags data for the game as a sub-class to ScoreboardData
    like no_hitter and perfect_game
    """
    def __init__(self, game: Game):
        self.no_hitter = game.gameData.flags.no_hitter
        self.perfect_game = game.gameData.flags.perfect_game

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the Flags object

        Returns:
            dict: Dictionary representation of the Flags object
        """
        return {
            'no_hitter': self.no_hitter,
            'perfect_game': self.perfect_game
        }

class ProbablePitchers:
    """
    Contains the probable pitcher data for the game as a sub-class to
    ScoreboardData
    """
    def __init__(self, game: Game):
        self._get_away(game)
        self._get_home(game)

    def _get_away(self, game: Game) -> str:
        away = game.gameData.probablePitchers.get('away', None)

        if away is None:
            self.away = 'TBD'
            self.away_era = '-.--'
            return None

        away_id = away['id']
        self.away = get_player_last_name(game, away_id)

        away_boxscore = game.liveData.boxscore.teams.away.players
        self.away_era = away_boxscore[f'ID{away_id}']['seasonStats']['pitching']['era']
        return None

    def _get_home(self, game: Game) -> str:
        home = game.gameData.probablePitchers.get('home', None)

        if home is None:
            self.home = 'TBD'
            self.home_era = '-.--'
            return None

        home_id = home['id']
        self.home = get_player_last_name(game, home_id)

        home_boxscore: List[dict] = game.liveData.boxscore.teams.home.players
        self.home_era = home_boxscore[f'ID{home_id}']['seasonStats']['pitching']['era']
        return None

    def to_dict(self) -> dict:
        """Return a dictionary representation of the ProbablePitchers object

        Returns:
            dict: Dictionary representation of the ProbablePitchers object
        """
        return {
            'away': self.away,
            'home': self.home,
            'away_era': self.away_era,
            'home_era': self.home_era
        }

class PitcherDecisions:
    """
    Contains the pitcher decisions data for the game as a sub-class to
    ScoreboardData
    """
    def __init__(self, game: Game):
        if game.liveData.decisions is None:
            self.win = None
            self.loss = None
            self.save = None
            self.win_summary = None
            self.loss_summary = None
            self.save_summary = None
            return None

        win_id = game.liveData.decisions.winner.id
        loss_id = game.liveData.decisions.loser.id

        self.win = get_player_last_name(game, win_id)
        self.loss = get_player_last_name(game, loss_id)

        away_score = game.liveData.linescore.teams.away.runs
        home_score = game.liveData.linescore.teams.home.runs

        away_team = game._game_dict['liveData']['boxscore']['teams']['away']['players']
        home_team = game._game_dict['liveData']['boxscore']['teams']['home']['players']

        if (win_id is None) or (loss_id is None):
            self.win_summary = None
            self.loss_summary = None
            self.save = None
            self.save_summary = None
            return None

        if away_score > home_score:
            w = away_team[f'ID{win_id}']['seasonStats']['pitching']['wins']
            l = away_team[f'ID{win_id}']['seasonStats']['pitching']['losses']
            self.win_summary = f'{w}-{l}'

            w = home_team[f'ID{loss_id}']['seasonStats']['pitching']['wins']
            l = home_team[f'ID{loss_id}']['seasonStats']['pitching']['losses']
            self.loss_summary = f'{w}-{l}'
        else:
            w = home_team[f'ID{win_id}']['seasonStats']['pitching']['wins']
            l = home_team[f'ID{win_id}']['seasonStats']['pitching']['losses']
            self.win_summary = f'{w}-{l}'

            w = away_team[f'ID{loss_id}']['seasonStats']['pitching']['wins']
            l = away_team[f'ID{loss_id}']['seasonStats']['pitching']['losses']
            self.loss_summary = f'{w}-{l}'

        if game.liveData.decisions.save is None:
            self.save = None
            self.save_summary = None
            return None

        save_id = game.liveData.decisions.save.id
        self.save = get_player_last_name(game, save_id)

        if away_score > home_score:
            save_team = game._game_dict['liveData']['boxscore']['teams']['away']['players']
            s = save_team[f'ID{save_id}']['seasonStats']['pitching']['saves']
            self.save_summary = f'{s}'
        else:
            save_team = game._game_dict['liveData']['boxscore']['teams']['home']['players']
            s = save_team[f'ID{save_id}']['seasonStats']['pitching']['saves']
            self.save_summary = f'{s}'

        return None

    def to_dict(self) -> dict:
        """Return a dictionary representation of the PitcherDecisions object

        Returns:
            dict: Dictionary representation of the PitcherDecisions object
        """
        return {
            'win': self.win,
            'loss': self.loss,
            'save': self.save,
            'win_summary': self.win_summary,
            'loss_summary': self.loss_summary,
            'save_summary': self.save_summary
        }

class Matchup:
    """
    Contains the matchup data for the game as a sub-class to ScoreboardData
    """
    def __init__(self, game: Game):
        self._game = game

        batter = game.liveData.linescore.offense.batter
        pitcher = game.liveData.linescore.defense.pitcher

        if (batter is None) or (pitcher  is None):
            self._none()
            return

        batter_id = batter.id
        pitcher_id = pitcher.id

        self.batter = get_player_last_name(game, batter_id)
        self.pitcher = get_player_last_name(game, pitcher_id)

        isTopInning = game.liveData.linescore.isTopInning
        outs = game.liveData.linescore.outs
        third_out = False
        if outs == 3:
            # If 3 outs in inning then the batter and pitcher are the
            # next half inning's batter and pitcher
            third_out = True

        if game.liveData.linescore.outs == 3:
            # If 3 outs in inning then the batter and pitcher are the
            # next half inning's batter and pitcher
            isTopInning = not isTopInning

        away_team = game._game_dict['liveData']['boxscore']['teams']['away']['players']
        home_team = game._game_dict['liveData']['boxscore']['teams']['home']['players']

        try:
            if (isTopInning ^ third_out) is True:
                self.pitcher_pitches = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_strikes = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikes"]
                self.pitcher_era = home_team[f"ID{pitcher_id}"]["seasonStats"]["pitching"]["era"]
                self.pitcher_walks = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["baseOnBalls"]
                self.pitcher_strike_outs = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikeOuts"]
                self.pitcher_innings_pitched = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["inningsPitched"]
                self.pitcher_hits_allowed = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["hits"]
                self.pitcher_runs_allowed = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["runs"]
                self.pitcher_earned_runs_allowed = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["earnedRuns"]
                self.batter_hits = away_team[f'ID{batter_id}']['stats']['batting']['hits']
                self.batter_at_bats = away_team[f'ID{batter_id}']['stats']['batting']['atBats']
                self.batter_avg = away_team[f'ID{batter_id}']['seasonStats']['batting']['avg']
                self.batter_slg = away_team[f'ID{batter_id}']['seasonStats']['batting']['slg']
                self.batter_ops = away_team[f'ID{batter_id}']['seasonStats']['batting']['ops']
            elif (isTopInning ^ third_out) is False:
                self.pitcher_pitches = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_strikes = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikes"]
                self.pitcher_era = away_team[f"ID{pitcher_id}"]["seasonStats"]["pitching"]["era"]
                self.pitcher_walks = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["baseOnBalls"]
                self.pitcher_strike_outs = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikeOuts"]
                self.pitcher_innings_pitched = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["inningsPitched"]
                self.pitcher_hits_allowed = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["hits"]
                self.pitcher_runs_allowed = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["runs"]
                self.pitcher_earned_runs_allowed = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["earnedRuns"]
                self.batter_hits = home_team[f'ID{batter_id}']['stats']['batting']['hits']
                self.batter_at_bats = home_team[f'ID{batter_id}']['stats']['batting']['atBats']
                self.batter_avg = home_team[f'ID{batter_id}']['seasonStats']['batting']['avg']
                self.batter_slg = home_team[f'ID{batter_id}']['seasonStats']['batting']['slg']
                self.batter_ops = home_team[f'ID{batter_id}']['seasonStats']['batting']['ops']
        except KeyError:
            # Sometimes mlb messes up and the inning state does not
            # match the batter and pitcher. This is a easy bodged fix
            if (isTopInning ^ third_out) is False:
                self.pitcher_pitches = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_strikes = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikes"]
                self.pitcher_era = home_team[f"ID{pitcher_id}"]["seasonStats"]["pitching"]["era"]
                self.pitcher_walks = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["baseOnBalls"]
                self.pitcher_strike_outs = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikeOuts"]
                self.pitcher_innings_pitched = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["inningsPitched"]
                self.pitcher_hits_allowed = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["hits"]
                self.pitcher_runs_allowed = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["runs"]
                self.pitcher_earned_runs_allowed = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["earnedRuns"]
                self.batter_hits = away_team[f'ID{batter_id}']['stats']['batting']['hits']
                self.batter_at_bats = away_team[f'ID{batter_id}']['stats']['batting']['atBats']
                self.batter_avg = away_team[f'ID{batter_id}']['seasonStats']['batting']['avg']
                self.batter_slg = away_team[f'ID{batter_id}']['seasonStats']['batting']['slg']
                self.batter_ops = away_team[f'ID{batter_id}']['seasonStats']['batting']['ops']
            elif (isTopInning ^ third_out) is True:
                self.pitcher_pitches = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_strikes = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikes"]
                self.pitcher_era = away_team[f"ID{pitcher_id}"]["seasonStats"]["pitching"]["era"]
                self.pitcher_walks = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["baseOnBalls"]
                self.pitcher_strike_outs = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["strikeOuts"]
                self.pitcher_innings_pitched = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["inningsPitched"]
                self.pitcher_hits_allowed = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["hits"]
                self.pitcher_runs_allowed = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["runs"]
                self.pitcher_earned_runs_allowed = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["earnedRuns"]
                self.batter_hits = home_team[f'ID{batter_id}']['stats']['batting']['hits']
                self.batter_at_bats = home_team[f'ID{batter_id}']['stats']['batting']['atBats']
                self.batter_avg = home_team[f'ID{batter_id}']['seasonStats']['batting']['avg']
                self.batter_slg = home_team[f'ID{batter_id}']['seasonStats']['batting']['slg']
                self.batter_ops = home_team[f'ID{batter_id}']['seasonStats']['batting']['ops']

        return None

    def _none(self):
            self.batter = None
            self.batter_hits = None
            self.batter_at_bats = None
            self.batter_avg = None
            self.batter_slg = None
            self.batter_ops = None
            self.pitcher = None
            self.pitcher_pitches = None
            self.pitcher_strikes = None
            self.pitcher_era = None
            self.pitcher_walks = None
            self.pitcher_strike_outs = None
            self.pitcher_innings_pitched = None
            self.pitcher_hits_allowed = None
            self.pitcher_runs_allowed = None
            self.pitcher_earned_runs_allowed = None

    def to_dict(self) -> dict:
        """Return a dictionary representation of the Matchup object

        Returns:
            dict: Dictionary representation of the Matchup object
        """
        return {
            'batter': {
                'name': self.batter,
                'hits': self.batter_hits,
                'at_bats': self.batter_at_bats,
                'avg': self.batter_avg,
                'slg': self.batter_slg,
                'ops': self.batter_ops
            },
            'pitcher': {
                'name': self.pitcher,
                'era': self.pitcher_era,
                'pitches': self.pitcher_pitches,
                'strikes': self.pitcher_strikes,
                'walks': self.pitcher_walks,
                'strike_outs': self.pitcher_strike_outs,
                'innings_pitched': self.pitcher_innings_pitched,
                'hits_allowed': self.pitcher_hits_allowed,
                'runs_allowed': self.pitcher_runs_allowed,
                'earned_runs_allowed': self.pitcher_earned_runs_allowed
            }
        }

class Count:
    """
    Contains the count data for the game as a sub-class to ScoreboardData
    """
    def __init__(self, game: Game):
        self.balls = game.liveData.linescore.balls
        self.strikes = game.liveData.linescore.strikes
        self.outs = game.liveData.linescore.outs

        if self.balls is None:
            self.balls = 0

        if self.strikes is None:
            self.strikes = 0

        if self.outs is None:
            self.outs = 0

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the Count object

        Returns:
            dict: Dictionary representation of the Count object
        """
        return {
            'balls': self.balls,
            'strikes': self.strikes,
            'outs': self.outs
        }

class Team:
    """
    Contains the team data for the game as a sub-class to Score
    """
    def __init__(self, game: Game, df, team: str):
        is_top_inning: bool = True if team == 'away' else False

        gamedata = game.gameData.teams
        gamedata = getattr(gamedata, team)
        self.abv = gamedata.abbreviation
        self.location = gamedata.location_name
        self.name = gamedata.teamName
        self.id = gamedata.id

        livedata_teams = game.liveData.linescore.teams
        livedata_teams = getattr(livedata_teams, team)
        self.runs = livedata_teams.runs
        self.hits = livedata_teams.hits
        self.errors = livedata_teams.errors
        self.left_on_base = livedata_teams.left_on_base

        if df.empty:
            self.xba = 0
            self.xslg = 0
        else:
            self.xba = df.loc[(df['is_top_inning'] == is_top_inning)]['batted_ball_xba'].mean()
            self.xslg = df.loc[(df['is_top_inning'] == is_top_inning)]['batted_ball_xslg'].mean()

        if pd.isna(self.xba):
            self.xba = 0
        if pd.isna(self.xslg):
            self.xslg = 0

        standings = ScoreboardStandings(self.abv)
        self.wins = standings.wins
        self.losses = standings.losses
        self.division_rank = standings.division_rank
        self.games_back = standings.games_back
        self.streak = standings.streak

        # maybe i shouldnt do this but its to catch pregame suspensions
        if self.runs is None:
            self.runs = 0

        if self.hits is None:
            self.hits = 0

        if self.errors is None:
            self.errors = 0

        if self.left_on_base is None:
            self.left_on_base = 0

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the Team object

        Returns:
            dict: Dictionary representation of the Team object
        """
        return {
            'abv': self.abv,
            'location': self.location,
            'name': self.name,
            'runs': self.runs,
            'hits': self.hits,
            'errors': self.errors,
            'left_on_base': self.left_on_base,
            'xba': self.xba,
            'xslg': self.xslg,
            'wins': self.wins,
            'losses': self.losses,
            'division_rank': self.division_rank,
            'games_back': self.games_back,
            'streak': self.streak
        }

class PitchDetails:
    """
    Contains the pitch details data for the game as a sub-class to Scoreboard
    """
    def __init__(self, game: Game, df: pd.DataFrame):
        if game.liveData.plays.allPlays == []:
            # new game but no pitches yet
            self.description = None
            self.speed = None
            self.type = None
            self.zone = None
            self.break_horizontal = None
            self.break_vertical = None
            self.break_vertical_induced = None
            self.pitch_hand = None
            self.umpire_missed_call = None
            # self.spin_rate = None
            return None

        if game.liveData.plays.allPlays[-1].playEvents == []:
            # new batter but no pitch yet
            at_bat = game.liveData.plays.allPlays[-2]
        else:
            at_bat = game.liveData.plays.allPlays[-1]
        pitch =  at_bat.playEvents[-1]

        if pitch.is_pitch is False:
            self.description = None
            self.speed = None
            self.type = None
            self.zone = None
            self.break_horizontal = None
            self.break_vertical = None
            self.break_vertical_induced = None
            self.pitch_hand = None
            self.umpire_missed_call = None
            # self.spin_rate = None
            return None

        self.description = pitch.details.description
        self.speed = pitch.pitch_data.startSpeed
        self.zone = pitch.pitch_data.zone
        self.pitch_hand = at_bat.matchup.pitch_hand.code

        run_favor = df.iloc[-1]['run_favor']
        if (run_favor == 0) or (pd.isna(run_favor)):
            self.umpire_missed_call = False
        else:
            run_favor = abs(run_favor)
            self.umpire_missed_call = True

        if not pitch.pitch_data.breaks:
            self.break_horizontal = None
            self.break_vertical = None
            self.break_vertical_induced = None
        else:
            self.break_horizontal = pitch.pitch_data.breaks.breakHorizontal
            self.break_vertical = pitch.pitch_data.breaks.breakVertical
            self.break_vertical_induced = pitch.pitch_data.breaks.breakVerticalInduced

        if pitch.details.type is not None:
            self.type = pitch.details.type.description
        else:
            self.type = None

        # spin rate is incosinstently available
        # self.spin_rate = pitch.pitchData.spinRate

        return None

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the PitchDetails object

        Returns:
            dict: Dictionary representation of the PitchDetails object
        """
        return {
            'description': self.description,
            'speed': self.speed,
            'type': self.type,
            'zone': self.zone,
            'break_horizontal': self.break_horizontal,
            'break_vertical': self.break_vertical,
            'break_vertical_induced': self.break_vertical_induced,
            'pitch_hand': self.pitch_hand,
            'umpire_missed_call': self.umpire_missed_call
            # 'spin_rate': self.spin_rate
        }

class HitDetails:
    """
    Contains the hit details data for the game as a sub-class
    """
    def __init__(self, df: pd.DataFrame):
        if df.empty:
            self._none()
            return None
        pitch = df.iloc[-1]

        self.exit_velo = pitch.get('batted_ball_launch_speed', None)
        self.launch_angle = pitch.get('batted_ball_launch_angle', None)
        self.distance = pitch.get('batted_ball_total_distance',  None)
        self.xba = pitch.get('batted_ball_xba', None)
        self.xslg = pitch.get('batted_ball_xslg', None)

        if pd.isna(self.exit_velo):
            self._none()

        self.xba = float(self.xba) if self.xba is not None else None
        self.xslg = float(self.xslg) if self.xslg is not None else None

        return None

    def _none(self):
        self.exit_velo = None
        self.launch_angle = None
        self.distance = None
        self.xba = None
        self.xslg = None

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the HitDetails object

        Returns:
            dict: Dictionary representation of the HitDetails object
        """
        return {
            'exit_velo': self.exit_velo,
            'launch_angle': self.launch_angle,
            'distance': self.distance,
            'xba': self.xba,
            'xslg': self.xslg,
        }

class RunExpectancy:
    """
    Contains the run expectancy data for the game as a sub-class to Scoreboard
    """
    def __init__(self, game: Game):
        if game.liveData.plays.allPlays == []:
            # No plays yet
            self.average_runs = None
            self.to_score = None
            return

        at_bat = game.liveData.plays.allPlays[-1]

        balls = game.liveData.linescore.balls
        strikes = game.liveData.linescore.strikes
        outs = game.liveData.linescore.outs

        if outs == 3:
            self.average_runs = 0
            self.to_score = 0
            return

        runners = Runners()
        runners.end_at_bat(at_bat)
        runners = int(runners)

        is_first_base = bool(runners & 1)
        is_second_base = bool(runners & 2)
        is_third_base = bool(runners & 4)

        state = ((re640['balls'] == balls) &
                (re640['strikes'] == strikes) &
                (re640['outs'] == outs) &
                (re640['is_first_base'] == is_first_base) &
                (re640['is_second_base'] == is_second_base) &
                (re640['is_third_base'] == is_third_base))

        self.average_runs = re640[state]['average_runs'].iloc[0]

        no_score = re640[state]['0 runs'].iloc[0]
        count = re640[state]['count'].iloc[0]

        if count > 0:
            self.to_score = 1 - (no_score / count)
        else:
            self.to_score = -1 # No data

        self.average_runs = float(self.average_runs)
        self.to_score = float(self.to_score)

        return

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the RunExpectancy object

        Returns:
            dict: Dictionary representation of the RunExpectancy object
        """
        return {
            'average_runs': self.average_runs,
            'to_score': self.to_score
        }

class WinProbability:
    """
    Contains the win probability data for the game as a sub-class to ScoreboardData
    """
    def __init__(self, game: Game):
        """
        Calculate the win probability for the away team, home team, and a tie.
        The extras attribute is the probability of a tie after 9 innings.
        Important to note that the extras attribute is already distributed
        to away and home win probabilities.

        So this: away_win + home_win = 1
        not this: away_win + home_win + tie = 1

        Args:
            game (Game): The Game object
        """
        self.win_probability_away = None
        self.win_probability_home = None
        self.extras = None

        if game.liveData.plays.allPlays == []:
            # No plays yet
            self.win_probability = None
            return

        at_bat = game.liveData.plays.allPlays[-1]

        balls = game.liveData.linescore.balls
        strikes = game.liveData.linescore.strikes
        outs = game.liveData.linescore.outs

        runners = Runners()
        runners.end_at_bat(at_bat)
        runners = int(runners)

        is_first_base = bool(runners & 1)
        is_second_base = bool(runners & 2)
        is_third_base = bool(runners & 4)

        inning = game.liveData.linescore.currentInning
        inning = min(inning, 10) # extra innings, revert to 10th inning

        isTopInning = game.liveData.linescore.isTopInning

        home_score = game.liveData.linescore.teams.home.runs
        away_score = game.liveData.linescore.teams.away.runs
        home_lead = home_score - away_score

        if (inning >= 9) and (isTopInning is False) and (home_lead < 0) and (outs == 3):
            self.win_probability_home = 0
            self.win_probability_away = 1
            self.extras = 0
            return None

        if (inning >= 9) and (isTopInning is True) and (home_lead > 0) and (outs == 3):
            self.win_probability_home = 1
            self.win_probability_away = 0
            self.extras = 0
            return None

        if (inning >= 9) and (isTopInning is False) and (home_lead > 0):
            # Walk off win
            self.win_probability_away = 0
            self.win_probability_home = 1
            self.extras = 0
            return None

        state = (
            (wp780800['balls'] == balls) &
            (wp780800['strikes'] == strikes) &
            (wp780800['outs'] == outs) &
            (wp780800['is_first_base'] == is_first_base) &
            (wp780800['is_second_base'] == is_second_base) &
            (wp780800['is_third_base'] == is_third_base) &
            (wp780800['inning'] == inning) &
            (wp780800['is_top_inning'] == isTopInning) &
            (wp780800['home_lead'] == home_lead)
        )

        away_win = wp780800[state]['away_win'].iloc[0]
        home_win = wp780800[state]['home_win'].iloc[0]
        tie = wp780800[state]['tie'].iloc[0]

        # Split the tie between the two teams
        away_win = away_win + (tie / 2)
        home_win = home_win + (tie / 2)

        # Normalize to eliminate floating point errors (i think)
        self.win_probability_away = away_win / (away_win + home_win)
        self.win_probability_home = home_win / (away_win + home_win)
        self.extras = tie

        self.win_probability_away = float(self.win_probability_away)
        self.win_probability_home = float(self.win_probability_home)
        self.extras = float(self.extras)

        return None

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the WinProbability object

        Returns:
            dict: Dictionary representation of the WinProbability object
        """
        return {
            'away': self.win_probability_away,
            'home': self.win_probability_home,
            'extras': self.extras
        }

class UmpireDetails:
    """
    Contains the umpire data for the game as a sub-class to ScoreboardData
    """
    def __init__(self, df: pd.DataFrame) -> None:
        if df.empty:
            self.home_favor = 0
            self.home_wpa = 0
            self.num_missed = 0
            return

        self.home_favor = df['run_favor'].sum()
        self.home_wpa = df['wp_favor'].sum()
        self.num_missed = len(df.loc[(
            ~(pd.isna(df['run_favor'])) &
            (df['run_favor'] != 0)
        )])

        self.home_favor = float(self.home_favor)
        self.home_wpa = float(self.home_wpa)
        self.num_missed = int(self.num_missed)

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the UmpireDetails object
        Returns:
            dict: Dictionary representation of the UmpireDetails object
        """
        return {
            'num_missed': self.num_missed,
            'home_favor': self.home_favor,
            'home_wpa': self.home_wpa
        }

class BattingOrder:
    def __init__(self, game: Game, state: str):
        # if state != 'L':
        #     self.at_bat_index = None
        #     self.batting_order = None
        #     return

        self.is_top_inning = game.liveData.linescore.isTopInning
        self.at_bat_index: int = game.liveData.linescore.offense.batting_order

        if (self.is_top_inning is None) or (self.at_bat_index is None):
            self.batting_order = None
            return

        # sometimes at_bat_index is 10 when going back to top of order
        self.at_bat_index = 1 if self.at_bat_index == 10 else self.at_bat_index

        self.batting_order: List[dict] = []

        outs = game.liveData.linescore.outs
        third_out = True if outs == 3 else False

        team = 'away' if self.is_top_inning ^ third_out else 'home'

        team_box_score = game.liveData.boxscore.teams.__getattribute__(team)
        batting_order: List[int] = team_box_score.batting_order
        players = team_box_score.players

        for i, batter in enumerate(batting_order):
            order = i + 1
            last_name = get_player_last_name(game, batter)
            player_id = batter
            avg = players[f'ID{player_id}']['seasonStats']['batting']['avg']
            slg = players[f'ID{player_id}']['seasonStats']['batting']['slg']
            ops = players[f'ID{player_id}']['seasonStats']['batting']['ops']
            position = players[f'ID{player_id}']['position']['abbreviation']

            self.batting_order.append({
                'order': order,
                'last_name': last_name,
                'id': player_id,
                'avg': avg,
                'slg': slg,
                'ops': ops,
                'position': position,
            })

    def to_dict(self):
        return {
            'at_bat_index': self.at_bat_index,
            'batting_order': self.batting_order,
        }

class ScoreboardData:
    """
    A simplified version of the Game object which holds information
    that is displayed on the scoreboard. This object is used to
    easaily access the data needed to display the scoreboard and return
    changes in the data.
    """
    def __init__(self, gamepk: int = None, delay_seconds: int = 0):
        self.gamepk: int = gamepk
        self.delay_seconds: int = delay_seconds

        self.game = Game.get_game_from_pk(gamepk=self.gamepk,
            delay_seconds=delay_seconds)

        self.parser = GameParser(game=self.game)
        self.dataframe = self.parser.dataframe

        # success = False
        # n = 1

        # while success is False:
        #     try:
        #         self.game = Game.get_game_from_pk(gamepk=self.gamepk,
        #             delay_seconds=self.delay_seconds)
        #         success = True
        #     except requests.exceptions.ReadTimeout:
        #         time.sleep(2**n)
        #         n += 1
        #         if n > 5:
        #             raise Exception('multiple timeouts')

        self.abstractGameState: str = self.game.gameData.status.abstractGameState
        self.abstractGameCode: str = self.game.gameData.status.abstractGameCode
        self.detailedState: str = self.game.gameData.status.detailedState
        self.codedGameState: str = self.game.gameData.status.codedGameState
        self.statusCode: str = self.game.gameData.status.statusCode

        # See get/game.py/status for more info:
        self.game_state: str = self.game.gameData.status.game_state
        self.check_postponed()

        self.start_time: str = self.game.gameData.datetime.startTime

        self.inning: int = self.game.liveData.linescore.currentInning

        isTopInning = self.game.liveData.linescore.isTopInning

        if isTopInning is True:
            self.inning_state: str = 'T'
        else:
            self.inning_state: str = 'B'

        # If game is postponed or suspended, inning is None
        # Could define it in game.py but dont want to mess with other code
        if self.inning is None:
            self.inning = 1
            self.inning_state = 'T'

        self.probables = ProbablePitchers(game=self.game)
        self.decisions = PitcherDecisions(game=self.game)
        self.matchup = Matchup(game=self.game)
        self.count = Count(game=self.game)
        self.away = Team(game=self.game, df=self.dataframe, team='away')
        self.home = Team(game=self.game, df=self.dataframe, team='home')
        self.pitch_details = PitchDetails(game=self.game, df=self.dataframe)
        self.hit_details = HitDetails(df=self.dataframe)
        self.run_expectancy = RunExpectancy(game=self.game)
        self.win_probability = WinProbability(game=self.game)
        self.umpire = UmpireDetails(df=self.dataframe)
        self.batting_order = BattingOrder(game=self.game, state=self.game_state)
        self.flags = Flags(game=self.game)

        runners = Runners()
        runners.set_bases_from_offense(self.game.liveData.linescore.offense)
        self.runners = int(runners)

    def update(self, delay_seconds: int = None) -> 'ScoreboardData':
        """
        Update the ScoreboardData object with the new data

        Args:
            delay_seconds (int, optional): The number of seconds to delay
                the data retrieval. Defaults to None.
        """
        if delay_seconds is not None:
            self.delay_seconds = delay_seconds

        new_game = ScoreboardData(gamepk=self.gamepk,
                                  delay_seconds=self.delay_seconds)

        new_game.check_postponed()

        self.__dict__.update(new_game.__dict__)

        return new_game

    def update_return_difference(self, delay_seconds: int = None) -> dict:
        """Return the difference between the current ScoreboardData
        object as a dictionary
        Also updates itself with the new data

        Returns:
            dict: The difference between the current ScoreboardData object
        """

        old_game = copy.deepcopy(self)
        new_game = self.update(delay_seconds=delay_seconds)

        diff = dict_diff(old_game.to_dict(), new_game.to_dict())

        return diff

    def to_dict(self) -> dict:
        """Return a dictionary representation of the ScoreboardData object

        Returns:
            dict: Dictionary representation of the ScoreboardData object
        """
        return {'gamepk': self.gamepk,
                'game_state': self.game_state,
                'start_time': self.start_time,
                'inning': self.inning,
                'inning_state': self.inning_state,
                'away': self.away.to_dict(),
                'home': self.home.to_dict(),
                'probables': self.probables.to_dict(),
                'decisions': self.decisions.to_dict(),
                'matchup': self.matchup.to_dict(),
                'count': self.count.to_dict(),
                'pitch_details': self.pitch_details.to_dict(),
                'hit_details': self.hit_details.to_dict(),
                'run_expectancy': self.run_expectancy.to_dict(),
                'win_probability': self.win_probability.to_dict(),
                'umpire': self.umpire.to_dict(),
                'batting_order': self.batting_order.to_dict(),
                'flags': self.flags.to_dict(),
                'runners': self.runners}

    def check_postponed(self):
        """
        The data source does not indicate if a game is postponed. It only
        changes the start date of the game. To check if a game is postponed
        by comparing the local date to the     current date at the stadium.
        If the game start date is not the same    as the current date, then
        the function returns true as the game is postponed.
        """

        date = self.game.gameData.datetime.dateTime
        utc_offset = self.game.gameData.venue.timeZone.offset

        utc_offset = timedelta(hours=utc_offset)

        game_start_zulu = datetime.fromisoformat(date.rstrip('Z'))
        game_start_stadium = game_start_zulu + utc_offset

        local_time_zulu = datetime.now(timezone.utc)
        local_time_stadium = local_time_zulu + utc_offset

        if game_start_stadium.date() > local_time_stadium.date():
            self.game_state = 'S' # Suspended/Postponed

    def __repr__(self):
        return f'{self.away.abv} {self.away.runs} @ {self.home.abv} {self.home.runs}'

if __name__ == '__main__':
    x = ScoreboardData(gamepk=778192, delay_seconds=38)
    print(json.dumps(x.to_dict(), indent=4))

    # x = ScoreboardStandings('NYY')
    # print(x.__dict__)
