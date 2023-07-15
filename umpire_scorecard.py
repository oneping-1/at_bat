"""
Attempt to replicate Umpire Scorecards
Finds all missed calls from a game and prints them
along with favored runs (>0 = home favored/gained runs)
"""

from typing import List
from get.statsapi_plus import get_game_dict
from get.game import Game
import get

def umpire(gamePk=None, print_every_missed_call: bool = False) -> float:
    """
    Calculates favored runs for the home team for a given team

    Itterates through every pitch in a given game and finds pitches that the umpire missed
    When home_favor >0, umpire effectively gave the home team runs.
    When <0, gave runs to the away team

    print_every_missed_call will print the following for every missed call when set to True:
    1. Inning
    2. Pitcher and Batter
    3. Count
    4. Pitch Location
    5. Strike Zone Location
    6. Favor

    Args:
        gamePk (int): The gamePk for the game. Can be found on the MLB/MiLB website
        print_every_missed_call (bool, optional): Argument to print details of every missed call
            Defaults to False

    """
    if gamePk is None:
        raise ValueError('gamePk not Provided')

    game_dict = get_game_dict(gamePk=gamePk, delay_seconds=0)
    game = Game(game_dict)

    at_bat_lists = game.liveData.plays.allPlays

    is_top_inning: bool = True
    inning: int = 0
    runners: List[bool] = [False, False, False] # [First, Second, Third]

    home_favor: float = float(0) # >0 = home helped, away hurt

    for at_bat in at_bat_lists:
        if (is_top_inning != at_bat.about.isTopInning) or (inning != at_bat.about.inning):
            is_top_inning = bool(at_bat.about.isTopInning)
            inning = int(at_bat.about.inning)
            runners = [False, False, False]

        for i in at_bat.pitchIndex:
            pitch: get.game.PlayEvents = at_bat.playEvents[i]

            home_favor_delta = pitch.get_delta_home_favor_monte_carlo(runners, is_top_inning)
            home_favor += home_favor_delta

            if home_favor_delta != 0 and print_every_missed_call is True:
                print(_missed_pitch_details(at_bat, pitch, runners, home_favor_delta))

        if at_bat.matchup.postOnFirst is not None:
            runners[0] = True
        else:
            runners[0] = False

        if at_bat.matchup.postOnSecond is not None:
            runners[1] = True
        else:
            runners[1] = False

        if at_bat.matchup.postOnThird is not None:
            runners[2] = True
        else:
            runners[2] = False

    return home_favor

def _missed_pitch_details(at_bat: get.game.AllPlays,
                          pitch: get.game.PlayEvents,
                          runners: List[bool],
                          home_delta: float) -> str:

    to_print_str = ''

    to_print_str += f'{at_bat.about.halfInning.capitalize()} {at_bat.about.inning}\n'
    to_print_str += f'{at_bat.matchup.pitcher.fullName} to {at_bat.matchup.batter.fullName}\n'

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

    if pitch.details.code == 'C':
        to_print_str += f'{pitch.count.balls}-{pitch.count.strikes-1}, ball called strike\n'
    elif pitch.details.code == 'B':
        to_print_str += f'{pitch.count.balls-1}-{pitch.count.strikes}, strike called ball\n'


    to_print_str += (f'pX = {pitch.pitchData.coordinates.pX:.3f} | '
                     f'pZ = {pitch.pitchData.coordinates.pZ:.3f}\n')

    to_print_str += (f'pZ_bot = {pitch.pitchData.coordinates.pZ_bot:.3f} | '
                     f'pZ_top = {pitch.pitchData.coordinates.pZ_top:.3f}\n')

    to_print_str += f'Home Favor: {home_delta:5.3f}\n'

    return to_print_str

if __name__ == '__main__':
    #gamePk = input('Input gamePk: ')
    home_favor_final = umpire(gamePk=717415, print_every_missed_call=True)
    print()
    print(f'Total Home Favor: {home_favor_final:.3f}')
