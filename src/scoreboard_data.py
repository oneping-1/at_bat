from typing import Tuple
from datetime import datetime, timedelta, timezone
import copy
from src.game import Game
from src.runners import Runners
from src.umpire import Umpire
import json

def dict_diff(dict1: dict, dict2: dict) -> dict:
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
    player = game.gameData.players[f'ID{player_id}']
    return player['lastName']

class ProbablePitchers:
    def __init__(self, game: Game):
        away_id = game.gameData.probablePitchers['away']['id']
        home_id= game.gameData.probablePitchers['home']['id']

        self.away = get_player_last_name(game, away_id)
        self.home = get_player_last_name(game, home_id)

        self.away_era = game._game_dict['liveData']['boxscore']['teams']['away']['players'][f'ID{away_id}']['seasonStats']['pitching']['era']
        self.home_era = game._game_dict['liveData']['boxscore']['teams']['home']['players'][f'ID{home_id}']['seasonStats']['pitching']['era']

    def to_dict(self) -> dict:
        return {'away': self.away, 'home': self.home, 'away_era': self.away_era, 'home_era': self.home_era}

class PitcherDecisions:
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

        if away_score > home_score:
            w = game._game_dict['liveData']['boxscore']['teams']['away']['players'][f'ID{win_id}']['seasonStats']['pitching']['wins']
            l = game._game_dict['liveData']['boxscore']['teams']['away']['players'][f'ID{win_id}']['seasonStats']['pitching']['losses']
            self.win_summary = f'{w}-{l}'

            w = game._game_dict['liveData']['boxscore']['teams']['home']['players'][f'ID{loss_id}']['seasonStats']['pitching']['wins']
            l = game._game_dict['liveData']['boxscore']['teams']['home']['players'][f'ID{loss_id}']['seasonStats']['pitching']['losses']
            self.loss_summary = f'{w}-{l}'
        else:
            w = game._game_dict['liveData']['boxscore']['teams']['home']['players'][f'ID{win_id}']['seasonStats']['pitching']['wins']
            l = game._game_dict['liveData']['boxscore']['teams']['home']['players'][f'ID{win_id}']['seasonStats']['pitching']['losses']
            self.win_summary = f'{w}-{l}'

            w = game._game_dict['liveData']['boxscore']['teams']['away']['players'][f'ID{loss_id}']['seasonStats']['pitching']['wins']
            l = game._game_dict['liveData']['boxscore']['teams']['away']['players'][f'ID{loss_id}']['seasonStats']['pitching']['losses']
            self.loss_summary = f'{w}-{l}'

        if game.liveData.decisions.save is None:
            self.save = None
            self.save_summary = None
            return None

        save_id = game.liveData.decisions.save.id
        self.save = get_player_last_name(game, save_id)

        if away_score > home_score:
            s = game._game_dict['liveData']['boxscore']['teams']['away']['players'][f'ID{save_id}']['seasonStats']['pitching']['saves']
            self.save_summary = f'{s}'
        else:
            s = game._game_dict['liveData']['boxscore']['teams']['home']['players'][f'ID{save_id}']['seasonStats']['pitching']['saves']
            self.save_summary = f'{s}'

    def to_dict(self) -> dict:
        return {'win': self.win, 'loss': self.loss, 'save': self.save, 'win_summary': self.win_summary, 'loss_summary': self.loss_summary, 'save_summary': self.save_summary}

class Matchup:
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

        if isTopInning is True:
            self.batter_summary = game._game_dict['liveData']['boxscore']['teams']['away']['players'][f'ID{batter_id}']['stats']['batting']['summary'][:3]
            self.pitcher_summary = f'P:{game._game_dict["liveData"]["boxscore"]["teams"]["home"]["players"][f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]}'
        elif isTopInning is False:
            self.batter_summary = game._game_dict['liveData']['boxscore']['teams']['home']['players'][f'ID{batter_id}']['stats']['batting']['summary'][:3]
            self.pitcher_summary = f'P:{game._game_dict["liveData"]["boxscore"]["teams"]["away"]["players"][f"ID{pitcher_id}"]["stats"]["pitching"]["numberOfPitches"]}'
        else:
            raise ValueError('isTopInning is not a boolean')

    def to_dict(self) -> dict:
        return {'batter': self.batter, 'pitcher': self.pitcher, 'batter_summary': self.batter_summary, 'pitcher_summary': self.pitcher_summary}

class ScoreboardData:
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

        self.away_abv: str = self.game.gameData.teams.away.abbreviation
        self.home_abv: str = self.game.gameData.teams.home.abbreviation

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

        self.outs: int = self.game.liveData.linescore.outs

        runners = Runners()
        runners.set_bases_from_offense(self.game.liveData.linescore.offense)
        self.runners = int(runners)

        self.umpire = 'L'
        umpire = Umpire(gamepk=self.gamepk, delay_seconds=self.delay_seconds)
        umpire.calculate_game(method='monte')
        self.umpire: str = f'{repr(umpire)} ({umpire.num_missed_calls:d})'

    def _get_live_batter(self):
        if self.game.liveData.linescore.offense.batter is None:
            self.batter = None
            return 0

        # batter_endpoint = self.game.liveData.linescore.offense.batter.link
        # batter_response = requests.get(url + batter_endpoint, timeout=10)
        # self.batter = batter_response.json()['people'][0]['lastName']
        # return 0

        batter_id = self.game.liveData.linescore.offense.batter.id
        self.batter = self._get_last_name(batter_id)

    def _get_live_pitcher(self):
        if self.game.liveData.linescore.defense.pitcher is None:
            self.pitcher = None
            return 0

        # pitcher_endpoint = self.game.liveData.linescore.defense.pitcher.link
        # pitcher_response = requests.get(url + pitcher_endpoint, timeout=10)
        # self.pitcher = pitcher_response.json()['people'][0]['lastName']

        pitcher_id = self.game.liveData.linescore.defense.pitcher.id
        self.pitcher = self._get_last_name(pitcher_id)

    def _get_pitcher_decisions(self) -> int:
        if self.game.liveData.decisions is None:
            self.winning_pitcher = None
            self.losing_pitcher = None
            self.save_pitcher = None
            return 0

        winning_pitcher_id = self.game.liveData.decisions.winner.id
        losing_pitcher_id = self.game.liveData.decisions.loser.id


        self.winning_pitcher = self._get_last_name(winning_pitcher_id)
        self.losing_pitcher = self._get_last_name(losing_pitcher_id)


        if self.game.liveData.decisions.save is None:
            self.save_pitcher = None
            return 0

        save_pitcher_id = self.game.liveData.decisions.save.id
        self.save_pitcher = self._get_last_name(save_pitcher_id)

        return 0

    def get_updated_data_dict(self) -> dict:
        new_game = ScoreboardData(gamepk=self.gamepk,
                                  delay_seconds=self.delay_seconds)

        new_game.check_postponed()

        diff = dict_diff(self.to_dict(), new_game.to_dict())

        self = new_game

        return diff

    def to_dict(self) -> dict:
        return {'gamepk': self.gamepk,
                'game_state': self.game_state,
                'away_abv': self.away_abv,
                'home_abv': self.home_abv,
                'away_score': self.away_score,
                'home_score': self.home_score,
                'start_time': self.start_time,
                'inning': self.inning,
                'inning_state': self.inning_state,
                'probables': self.probables.to_dict(),
                'decisions': self.decisions.to_dict(),
                'matchup': self.matchup.to_dict(),
                'outs': self.outs,
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
        return f'{self.away_abv} {self.away_score} @ {self.home_abv} {self.home_score}'

if __name__ == '__main__':
    x = ScoreboardData(gamepk=745560)
    print(json.dumps(x.to_dict(), indent=4))
