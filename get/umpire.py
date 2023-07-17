from typing import List
from .game import Game, AllPlays, PlayEvents
from .runners import Runners
from .statsapi_plus import get_game_dict

class Umpire():
    def __init__(self,
                 missed_calls: int,
                 home_favor: float,
                 game: Game):

        self.missed_calls: int = missed_calls
        self.home_favor: float = home_favor
        self.game = game

def get_total_favored_runs(gamePk: int = None,
           print_missed_calls: bool = False,
           delay: float = 0,
           game_class: Game = None) -> float:
    """
    Calculates total favored runs for the home team for a given team

    Itterates through every pitch in a given game and finds pitches that
        the umpire missed.
    When home_favor >0, umpire effectively gave the home team runs.
    When <0, gave runs to the away team

    print_every_missed_call will print the following for every missed
        call when set to True:
    1. Inning
    2. Pitcher and Batter
    3. Count
    4. Pitch Location
    5. Strike Zone Location
    6. Favor

    Args:
        gamePk (int): The gamePk for the game. Can be found on the 
            MLB/MiLB website
        print_missed_calls (bool, optional): Argument to print 
            details of every missed call. Defaults to False
        delay_seconds (float, optional): How many seconds you want the
            scoreboard to be delayed by. Defaults to 0
        game_class (get.game.Game, optional): If this is calculated
            outside of the function, using this argument may cut down
            on runtime Defaults to None

    Returns:
        missed_calls (int): The number of missed calls by the umpire
        home_favor (float): The runs the umpire gave the home team
            by their missed calls
    """

    if game_class is not None:
        game = game_class
    else:
        if gamePk is None:
            raise ValueError('gamePk not Provided')
        game_dict = get_game_dict(gamePk=gamePk, delay_seconds=delay)
        game = Game(game_dict)

    missed_calls = 0

    runners: Runners = Runners()
    runners_int = int(runners)

    home_favor: float = float(0) # >0 = home helped, away hurt

    for at_bat in game.liveData.plays.allPlays:
        runners.place_runners(at_bat)
        isTopInning = at_bat.about.isTopInning

        for i in at_bat.pitchIndex:
            pitch: PlayEvents = at_bat.playEvents[i]

            home_delta = pitch.delta_favor_monte(runners_int, isTopInning)

            if home_delta != 0:
                home_favor += home_delta
                missed_calls += 1

                if print_missed_calls is True:
                    print(_missed_pitch_details(
                        at_bat, pitch, runners, home_delta))

    away_abv = game.gameData.teams.away.abbreviation
    home_abv =  game.gameData.teams.home.abbreviation

    print(f'Missed Calls: {missed_calls}')

    if home_favor < 0:
        print(f' +{home_favor:.2f} {away_abv}')
    else:
        print(f' +{home_favor:.2f} {home_abv}')

    return (missed_calls, home_favor)

def _missed_pitch_details(at_bat: AllPlays,
                          pitch: PlayEvents,
                          runners: List[bool],
                          home_delta: float) -> str:

    to_print_str = ''

    half_inn = at_bat.about.halfInning.capitalize()
    inning = at_bat.about.inning
    pitcher_name = at_bat.matchup.pitcher.fullName
    batter_name = at_bat.matchup.batter.fullName

    to_print_str += f'{half_inn} {inning}\n'
    to_print_str += f'{pitcher_name} to {batter_name}\n'

    if pitch.count.outs == 1:
        to_print_str += f'{pitch.count.outs} out, '
    else:
        to_print_str += f'{pitch.count.outs} outs, '

    if runners == [False, False, False]:
        to_print_str += 'bases empty\n'
    elif runners == [True, False, False]:
        to_print_str += 'runner on first\n'
    elif runners == [False, True, False]:
        to_print_str += 'runner on second\n'
    elif runners == [True, True, False]:
        to_print_str += 'runners on first and second\n'
    elif runners == [False, False, True]:
        to_print_str += 'runner on third\n'
    elif runners == [True, False, True]:
        to_print_str += 'runner on first and third\n'
    elif runners == [False, True, True]:
        to_print_str += 'runner on second and third\n'
    elif runners == [True, True, True]:
        to_print_str += 'bases loaded\n'

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

    to_print_str += f'Home Favor: {home_delta:5.3f}\n'

    return to_print_str