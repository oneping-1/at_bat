"""
This module contains the ScoreboardData class which is a simplified
version of the Game object which holds information that is displayed
on the scoreboard. This object is used to easaily access the data
needed to display the scoreboard and return changes in the data.

Raises:
    ValueError: If isTopInning is not a boolean
"""

import os
import csv
from datetime import datetime, timedelta, timezone
import json
from typing import List
from src.statsapi_plus import get_re640_dataframe, get_wp780800_dataframe
from src.game import Game
from src.runners import Runners
from src.umpire import Umpire
from src.standings import Standings

re640 = get_re640_dataframe()
wp780800 = get_wp780800_dataframe()

csv_path = os.path.join(os.path.dirname(os.path.relpath(__file__)), '..', 'csv')

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
    player = game.gameData.players[f'ID{player_id}']
    return player['lastName']

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

        if game.gameData.status.game_state in ('P', 'F'):
            # game_state == 'F': batter is last batter to hit
            # but with 3 outs future checks will cause it to be the
            # wrong half inning
            self.batter = None
            self.pitcher = None
            self.batter_summary = None
            self.pitcher_summary = None
            return None

        batter_id = game.liveData.linescore.offense.batter.id
        pitcher_id = game.liveData.linescore.defense.pitcher.id

        self.batter = get_player_last_name(game, batter_id)
        self.pitcher = get_player_last_name(game, pitcher_id)

        isTopInning = game.liveData.linescore.isTopInning

        if game.liveData.linescore.outs == 3:
            # If 3 outs in inning then the batter and pitcher are the
            # next half inning's batter and pitcher
            isTopInning = not isTopInning

        away_team = game._game_dict['liveData']['boxscore']['teams']['away']['players']
        home_team = game._game_dict['liveData']['boxscore']['teams']['home']['players']

        try:
            if isTopInning is True:
                pitches = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_summary = f'P:{pitches}'
                self.batter_summary = away_team[f'ID{batter_id}']['stats']['batting']['summary'][:3]
            elif isTopInning is False:
                pitches = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_summary = f'P:{pitches}'
                self.batter_summary = home_team[f'ID{batter_id}']['stats']['batting']['summary'][:3]
            else:
                raise ValueError('isTopInning is not a boolean')
        except KeyError:
            # Sometimes mlb messes up and the inning state does not
            # match the batter and pitcher. This is a easy bodged fix
            if isTopInning is False:
                pitches = home_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_summary = f'P:{pitches}'
                self.batter_summary = away_team[f'ID{batter_id}']['stats']['batting']['summary'][:3]
            elif isTopInning is True:
                pitches = away_team[f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]
                self.pitcher_summary = f'P:{pitches}'
                self.batter_summary = home_team[f'ID{batter_id}']['stats']['batting']['summary'][:3]

        return None

    def to_dict(self) -> dict:
        """Return a dictionary representation of the Matchup object

        Returns:
            dict: Dictionary representation of the Matchup object
        """
        return {
            'batter': self.batter,
            'pitcher': self.pitcher,
            'batter_summary': self.batter_summary,
            'pitcher_summary': self.pitcher_summary
        }

class Count:
    """
    Contains the count data for the game as a sub-class to ScoreboardData
    """
    def __init__(self, game: Game):
        self.balls = game.liveData.linescore.balls
        self.strikes = game.liveData.linescore.strikes
        self.outs = game.liveData.linescore.outs

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
    def __init__(self, game: Game, team: str):
        self.abv = game.gameData._gameData['teams'][team]['abbreviation']
        self.location = game.gameData._gameData['teams'][team]['locationName']
        self.name = game.gameData._gameData['teams'][team]['teamName']
        self.id = game.gameData._gameData['teams'][team]['id']

        self.wins = None
        self.losses = None
        self.division_rank: int = None
        self.games_back: str = None

        self._get_standing_info()

    def _get_division(self) -> str:
        teams = os.path.join(csv_path, 'teams.csv')

        with open(teams, encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for _, abv, division in reader:
                if self.abv == abv:
                    return division

    def _get_standing_info(self):
        division = self._get_division()

        league = division[0]
        division = division[1]

        if league == 'A':
            standings = Standings.get_standings(league='AL')
        else:
            standings = Standings.get_standings(league='NL')

        if division == 'E':
            standings = standings.east
        elif division == 'C':
            standings = standings.central
        elif division == 'W':
            standings = standings.west

        for team in standings.team_records:
            if team.team.id == self.id:
                self.wins = team.wins
                self.losses = team.losses
                self.division_rank = team.division_rank
                self.games_back = team.games_back
                self.streak = team.streak.streakCode

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the Team object

        Returns:
            dict: Dictionary representation of the Team object
        """
        return {
            'abv': self.abv,
            'location': self.location,
            'name': self.name
        }

class PitchDetails:
    """
    Contains the pitch details data for the game as a sub-class to Scoreboard
    """
    def __init__(self, game: Game):
        if game.liveData.plays.allPlays == []:
            # new game but no pitches yet
            self.description = None
            self.speed = None
            self.type = None
            self.zone = None
            # self.spin_rate = None
            return None

        if game.liveData.plays.allPlays[-1].playEvents == []:
            # new batter but no pitch yet
            pitch = game.liveData.plays.allPlays[-2].playEvents[-1]
        else:
            pitch =  game.liveData.plays.allPlays[-1].playEvents[-1]

        if pitch.isPitch is False:
            self.description = None
            self.speed = None
            self.type = None
            self.zone = None
            # self.spin_rate = None
            return None

        self.description = pitch.details.description
        self.speed = pitch.pitchData.startSpeed
        self.zone = pitch.pitchData.zone

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
            'zone': self.zone
            # 'spin_rate': self.spin_rate
        }

class HitDetails:
    """
    Contains the hit details data for the game as a sub-class
    """
    def __init__(self, game: Game):
        pitch = None

        if game.liveData.plays.allPlays == []:
            # Game has not started
            self.exit_velo = None
            self.launch_angle = None
            self.distance = None
            return None

        if game.liveData.plays.allPlays[-1].playEvents == []:
            # No pitch in current at bat yet
            pitch = game.liveData.plays.allPlays[-2].playEvents[-1]
        else:
            pitch = game.liveData.plays.allPlays[-1].playEvents[-1]

        if pitch.isPitch is False:
            self.exit_velo = None
            self.launch_angle = None
            self.distance = None

        if pitch.hitData is None:
            self.exit_velo = None
            self.launch_angle = None
            self.distance = None
            return None

        self.exit_velo = pitch.hitData.launchSpeed
        self.launch_angle = pitch.hitData.launchAngle
        self.distance = pitch.hitData.totalDistance

        return None

    def to_dict(self) -> dict:
        """
        Return a dictionary representation of the HitDetails object

        Returns:
            dict: Dictionary representation of the HitDetails object
        """
        return {
            'exit_velo': self.exit_velo,
            'launch_angle': self.launch_angle,
            'distance': self.distance
        }

class UmpireDetails:
    """
    Contains the umpire data for the game as a sub-class to ScoreboardData
    """
    def __init__(self, game: Game) -> None:
        umpire = Umpire(game=game, method='monte')
        umpire.calculate_game()

        self.num_missed: int = umpire.num_missed_calls
        self.home_favor: float = umpire.home_favor
        self.home_wpa: float = umpire.home_wpa

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
        self.to_score = 1 - (no_score / count)

        if count == 0:
            print('divide by 0')

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

        self.game: Game = Game.get_game_from_pk(gamepk =self.gamepk,
                                                delay_seconds=self.delay_seconds)

        self.abstractGameState: str = self.game.gameData.status.abstractGameState
        self.abstractGameCode: str = self.game.gameData.status.abstractGameCode
        self.detailedState: str = self.game.gameData.status.detailedState
        self.codedGameState: str = self.game.gameData.status.codedGameState
        self.statusCode: str = self.game.gameData.status.statusCode

        # See get/game.py/status for more info:
        self.game_state: str = self.game.gameData.status.game_state
        self.check_postponed()

        self.away_score: int = self.game.liveData.linescore.teams.away.runs
        self.home_score: int = self.game.liveData.linescore.teams.home.runs

        if self.away_score is None:
            self.away_score = 0
        if self.home_score is None:
            self.home_score = 0

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
        self.away = Team(game=self.game, team='away')
        self.home = Team(game=self.game, team='home')
        self.pitch_details = PitchDetails(game=self.game)
        self.hit_details = HitDetails(game=self.game)
        self.umpire = UmpireDetails(game=self.game)
        self.run_expectancy = RunExpectancy(game=self.game)
        self.win_probability = WinProbability(game=self.game)
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

    def get_updated_data_dict(self, delay_seconds: int = None) -> dict:
        """Return the difference between the current ScoreboardData
        object as a dictionary
        Also updates itself with the new data

        Returns:
            dict: The difference between the current ScoreboardData object
        """

        new_game = self.update(delay_seconds=delay_seconds)

        diff = dict_diff(self.to_dict(), new_game.to_dict())

        self.__dict__.update(new_game.__dict__)

        return diff

    def to_dict(self) -> dict:
        """Return a dictionary representation of the ScoreboardData object

        Returns:
            dict: Dictionary representation of the ScoreboardData object
        """
        return {'gamepk': self.gamepk,
                'game_state': self.game_state,
                'away_score': self.away_score,
                'home_score': self.home_score,
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
                'umpire': self.umpire.to_dict(),
                'run_expectancy': self.run_expectancy.to_dict(),
                'win_probability': self.win_probability.to_dict(),
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
        return f'{self.away.abv} {self.away_score} @ {self.home.abv} {self.home_score}'

if __name__ == '__main__':
    x = ScoreboardData(gamepk=745455)
    print(json.dumps(x.to_dict(), indent=4))
