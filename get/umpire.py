from typing import List, Tuple
from get.game import Game, AllPlays, PlayEvents
from get.runners import Runners
from get.statsapi_plus import get_game_dict


class Umpire():
    """
    Holds info for each game and their missed calls.

    Attribues:
        game (get.game.Game): Game class with all info
        gamePk (int): gamePk number
        num_missed_calls (int): The number of missed calls made
            in the game
        home_favor (float): The number of runs awarded to the home team
            in the game
        away_abv (str): The abbreviation of the away team
        home_abv (str): The abbreviation of the home team
    """
    def __init__(self,
                 gamePk: int = None,
                 game: Game = None):

        if game is not None:
            self.game = game
        elif gamePk is not None:
            game_dict = get_game_dict(gamePk)
            self.game = Game(game_dict)
        else:
            raise ValueError('gamePk and game arguments not provided')

        self.gamePk = game.gamePk
        self.num_missed_calls = 0
        self.missed_calls: List[PlayEvents] = []
        self.home_favor = 0
        self.away_abv = game.gameData.teams.away.abbreviation
        self.home_abv = game.gameData.teams.home.abbreviation

    def set(self,
            print_missed_calls: bool = False
            ) -> Tuple[int, float, List[PlayEvents]]:
        """
        Basically a front to Umpire.find_missed_calls that automatically
        inputs its output into instance variables
        """

        stats = self.find_missed_calls(game=self.game,
                                     print_missed_calls=print_missed_calls)

        self.num_missed_calls, self.home_favor, self.missed_calls = stats

    @classmethod
    def find_missed_calls(cls,
                          game: Game = None,
                          gamePk: int = None,
                          print_missed_calls: bool = False
                          ) -> Tuple[int, float, List[PlayEvents]]:
        """
        Calculates total favored runs for the home team for a given team

        Itterates through every pitch in a given game and finds pitches
            that the umpire missed.
        When home_favor >0, umpire effectively gave the home team runs.
        When <0, gave runs to the away team

        print_every_missed_call will print the following for every missed
            call when set to True. Defaults to False:
        1. Inning
        2. Pitcher and Batter
        3. Count
        4. Pitch Location
        5. Strike Zone Location
        6. Favor

        Returns:
            num_missed_calls (int): The number of missed calls by the umpire
            home_favor (float): The runs the umpire gave the home team
                by their missed calls
            missed_calls (List[PlayEvents]): A list of missed calls
                with each element a Missed_Calls class

        Raises:
            ValueError: If game and gamePk are not provided
        """
        if game is None and gamePk is not None:
            game_dict = get_game_dict(gamePk)
            game = Game(game_dict)
        elif game is None and gamePk is None:
            raise ValueError('game and gamePk not provided')

        j = 1

        home_favor: float = 0
        missed_calls: List[PlayEvents] = []
        runners = Runners()

        for at_bat in game.liveData.plays.allPlays:
            runners.new_batter(at_bat)
            runners_int = int(runners)
            isTopInning = at_bat.about.isTopInning

            for i in at_bat.pitchIndex:
                pitch: PlayEvents = at_bat.playEvents[i]
                home_delta = pitch.delta_favor_monte(runners_int, isTopInning)

                if home_delta != 0:
                    home_favor += home_delta
                    missed_calls.append(pitch)

                    if print_missed_calls is True:
                        print(cls._missed_pitch_details(
                            at_bat, runners, pitch, home_delta,j))
                        j += 1

            runners.end_batter(at_bat)

        return (len(missed_calls), home_favor, missed_calls)

    @classmethod
    def _missed_pitch_details(cls,
                            at_bat: AllPlays,
                            runners: Runners,
                            pitch: PlayEvents,
                            home_delta: float,
                            i: int) -> str:

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


        to_print_str += (f'pX = {pitch.pitchData.coordinates.pX:.3f} | '
                        f'pZ = {pitch.pitchData.coordinates.pZ:.3f}\n')

        to_print_str += (f'bot = {pitch.pitchData.coordinates.pZ_bot:.3f} | '
                        f'top = {pitch.pitchData.coordinates.pZ_top:.3f}\n')

        to_print_str += f'Home Favor: {home_delta:4.2f}\n'

        return to_print_str


    def __len__(self):
        return len(self.missed_calls)


    def __str__(self):
        prt_str = ''

        prt_str += f'{len(self.missed_calls)} Missed Calls. '
        prt_str += f'{self.home_favor} Home Favor'

        return prt_str
