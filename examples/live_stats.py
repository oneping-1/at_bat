"""
This module will print the details for the most recent pitch in a MLB
and MiLB games provided with a gamePk from the MLB/MiLB website

You can find the gamePk for a given game by going to the 'Gameday'
section of the desired game and by looking for a string of 6 consecutive
numbers in the url.

Functions:
    print_last_pitch(gamePk, delay_seconds): Prints live stats for the
        given game based off the gamePk argument with a delay in
        seconds if delay_seconds argument is provided
    main(): Gets gamePk and delay_seconds from command line arguments
        and prompts user for input if either command line argument is
        provided
"""

import curses
import argparse
from typing import Tuple
from at_bat.game import Game, PlayEvents, AllPlays
from at_bat.statsapi_plus import get_game_dict, get_re640_dataframe
from at_bat.umpire import Umpire
from at_bat.runners import Runners
from at_bat.fifo import FIFO

re640 = get_re640_dataframe()

def print_last_pitch(gamePk: int = None, delay_seconds: float = 0):
    """
    Prints the following for the latest pitch:

    1. Away/Home teams + score
    2. Inning
    3. Count
    4. Pitcher and Batter name

    Pitch Details:
    5. Pitch Result
    6. Pitch Speed + Name
    7. If pitch was in zone + home favor if missed call

    Hit Details:
    8. Exit Velocity
    9. Launch Angle
    10. Total Distance

    Args:
        gamePk (int): The gamePk for the desired
        delay (float, optional): The numbers of seconds you want the
            output to be delayed. Useful so that pitch info does not
            show up before pitch is thrown on TV. Defaults to 0
    """
    print(f'gamePk: {gamePk}, delay: {delay_seconds}')

    if gamePk is None:
        raise ValueError('gamePk not provided')

    clr = ' ' * 40

    god = curses.initscr()
    god.clear()
    fifo = FIFO(5)

    while True:
        game = Game(get_game_dict(gamepk=gamePk, delay_seconds=delay_seconds))
        at_bat = game.liveData.plays.allPlays[-1]

        if fifo.contains(at_bat) is False:
            fifo.push(at_bat)

            if len(at_bat.playEvents) > 0:
                pitch = at_bat.playEvents[-1]

                i = 0
                for line in _get_game_details(game, at_bat):
                    god.addstr(i, 0, f'{line} {clr}')
                    i += 1

                for line in _get_at_bat_details(at_bat, pitch):
                    god.addstr(i, 0, f'{line} {clr}')
                    i += 1

                i += 1
                for line in _get_run_details(at_bat, pitch):
                    god.addstr(i, 0, f'{line} {clr}')
                    i += 1

                i += 1
                for line in _get_umpire_details(game):
                    god.addstr(i, 0, f'{line} {clr}')
                    i += 1

                i += 1
                for line in _get_pitch_details(pitch):
                    god.addstr(i, 0, f'{line} {clr}')
                    i += 1

                i += 1
                for line in _get_hit_details(pitch):
                    god.addstr(i, 0, f'{line} {clr}')
                    i += 1

                god.refresh()


def _get_game_details(game: Game, at_bat: AllPlays) -> Tuple[str, str]:
    away_team = game.gameData.teams.away.teamName
    away_score = at_bat.result.awayScore
    home_team = game.gameData.teams.home.teamName
    home_score = at_bat.result.homeScore

    half_inn = at_bat.about.halfInning.capitalize()
    inning = at_bat.about.inning

    line_0 = f'{away_team} ({away_score}) at {home_team} ({home_score})'
    line_1 = f'{half_inn} {inning}'
    return (line_0, line_1)


def _get_at_bat_details(at_bat: AllPlays,
                        pitch: PlayEvents) -> Tuple[str, str, str]:
    pitcher = at_bat.matchup.pitcher.fullName
    batter = at_bat.matchup.batter.fullName

    balls = pitch.count.balls
    strikes = pitch.count.strikes
    outs = pitch.count.outs

    runners = Runners()
    # end_batter method sets the runners which is why its used here
    # might have errors with walks?
    runners.end_at_bat(at_bat)

    line_0 = f'{pitcher} to {batter}'
    line_1 = f'{balls}-{strikes} | {outs} Outs'
    line_2 = f'{str(runners).capitalize()}'

    return (line_0, line_1, line_2)

def _get_run_details_state(at_bat: AllPlays, pitch: PlayEvents) -> bool:
    balls = pitch.count.balls
    strikes = pitch.count.strikes
    outs = pitch.count.outs
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

    return state

def _get_run_details(at_bat: AllPlays, pitch: PlayEvents
                     ) -> Tuple[str, str, str, str, str, str]:

    state = _get_run_details_state(at_bat, pitch)

    run_exp = re640[state]['average_runs'].iloc[0]
    count = re640[state]['count'].iloc[0]

    runs = [0, 0, 0, 0] # 1+, 2+, 3+, 4+

    for i in range(0, 14):
        runs = re640[state][f'{i} runs'].iloc[0]

        if i >= 1:
            runs[0] += runs
        if i >= 2:
            runs[1] += runs
        if i >= 3:
            runs[2] += runs
        if i >= 4:
            runs[3] += runs

    line_0 = f'Expected Runs: {run_exp:.2f}'
    line_1 = f'1+ Runs: {runs[0] / count:.2f}'
    line_2 = f'2+ Runs: {runs[1] / count:.2f}'
    line_3 = f'3+ Runs: {runs[2] / count:.2f}'
    line_4 = f'4+ Runs: {runs[3] / count:.2f}'


    return (line_0, line_1, line_2, line_3, line_4)


def _get_umpire_details(game: Game) -> Tuple[str, str]:
    away_team = game.gameData.teams.away.abbreviation
    home_team = game.gameData.teams.home.abbreviation

    umpire = Umpire(game=game)
    umpire.calculate_game('monte')
    misses = umpire.num_missed_calls
    favor = umpire.home_favor

    line_0 = f'Missed Calls: {misses}'

    if favor < 0:
        line_1 = f'Ump Favor: {-favor:+5.2f} {away_team}'
    else:
        line_1 = f'Ump Favor: {favor:+5.2f} {home_team}'

    return (line_0, line_1)

def _get_pitch_details(pitch: PlayEvents) -> Tuple[str, str, str, str, str]:
    if pitch.isPitch is True:
        desc = pitch.details.description
        speed = pitch.pitchData.startSpeed
        pitch_type = pitch.details.type.description

        dx = pitch.pitchData.breaks.breakHorizontal
        idy = pitch.pitchData.breaks.breakVerticalInduced

        line_0 = 'Pitch Details: '
        line_1 = f'{desc}'
        line_2 = f'{speed} {pitch_type}'
        line_3 = f'Zone: {pitch.pitchData.zone}'
        line_4 = f'{pitch.pitchData.breaks.spinRate} RPM'
        line_5 = f'dx: {dx}'
        line_6 = f'idy: {idy}'
    else:
        desc = pitch.details.description

        line_0 = 'Pitch Details: '
        line_1 = f'{desc}'
        line_2 = ''
        line_3 = ''
        line_4 = ''
        line_5 = ''
        line_6 = ''

    return (line_0, line_1, line_2, line_3, line_4, line_5, line_6)


def _get_hit_details(pitch: PlayEvents) -> Tuple[str, str, str, str]:
    if pitch.hitData is not None:
        exit_velo = pitch.hitData.launchSpeed
        launch_angle = pitch.hitData.launchAngle
        distance = pitch.hitData.totalDistance

        line_0 = 'Hit Details:'
        line_1 = f'Exit Velo: {exit_velo}'
        line_2 = f'Launch Angle: {launch_angle}'
        line_3 = f'Total Dist: {distance}'
    else:
        line_0 = ''
        line_1 = ''
        line_2 = ''
        line_3 = ''

    return (line_0, line_1, line_2, line_3)


def main():
    """
    Main function that grabs system arguments and runs code
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gamepk', help = 'gamePk', type=int)
    parser.add_argument('-d', '--delay', help='delay in seconds', type=int)
    args = parser.parse_args()

    if args.gamepk is not None:
        gamePk = args.gamepk
    else:
        gamePk = int(input('gamePk: '))

    if args.delay is not None:
        delay = args.delay
    else:
        delay = float(input('delay: '))

    print_last_pitch(gamePk=gamePk, delay_seconds=delay)


if __name__ == '__main__':
    main()
