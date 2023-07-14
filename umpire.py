import statsapi
from get.game import Game
import get
from datetime import datetime, timedelta
from typing import List
import curses
import time

def _get_utc_time(delta_seconds=0):
    # Get the current time in UTC
    utc_time = datetime.utcnow()

    # Subtract the delta
    utc_time = utc_time - timedelta(seconds=delta_seconds)

    # Format the time
    formatted_time = utc_time.strftime('%Y%m%d_%H%M%S')

    return formatted_time

def _get_game_dict(gamePk=None, delta_seconds=0) -> dict:
    if gamePk is None:
        raise ValueError('gamePk not given')

    delay_time = _get_utc_time(delta_seconds=delta_seconds)
    data = statsapi.get('game', {'gamePk': gamePk, 'timecode': delay_time}, force=True)
    return data

def _missed_pitch_details(ab: get.game.AllPlays, pitch: get.game.PlayEvents, runners: List[bool], home_delta: float) -> str:
    s = ''

    s += f'{ab.about.halfInning.capitalize()} {ab.about.inning}\n'
    s += f'{ab.matchup.pitcher.fullName} to {ab.matchup.batter.fullName}\n'

    if pitch.count.outs == 1:
        s += f'{pitch.count.outs} out, '
    else:
        s += f'{pitch.count.outs} outs, '

    if runners == [False, False, False]:
        s += f'bases empty\n'
    elif runners == [True, False, False]:
        s += f'runner on first\n'
    elif runners == [False, True, False]:
        s += f'runner on second\n'
    elif runners == [True, True, False]:
        s += f'runners on first and second\n'
    elif runners == [False, False, True]:
        s += f'runner on third\n'
    elif runners == [True, False, True]:
        s += f'runner on first and third\n'
    elif runners == [False, True, True]:
        s += f'runner on second and third\n'
    elif runners == [True, True, True]:
        s += f'bases loaded\n'

    if pitch.details.code == 'C':
        s += f'{pitch.count.balls}-{pitch.count.strikes-1}, ball called strike\n'
    elif pitch.details.code == 'B':
        s += f'{pitch.count.balls-1}-{pitch.count.strikes}, strike called ball\n'

    s += f'pX = {pitch.pitchData.coordinates.pX:.3f} | pZ = {pitch.pitchData.coordinates.pZ:.3f}\n'
    s += f'pZ_bot = {pitch.pitchData.coordinates.pZ_bot:.3f} | pZ_top = {pitch.pitchData.coordinates.pZ_top:.3f}\n'

    s += f'{home_delta:5.3f}\n'

    return s

def umpire(gamePk=None, print_every_missed_call: bool = False) -> float:
    if gamePk is None:
        raise ValueError('gamePk not Provided')

    game_dict = _get_game_dict(gamePk=gamePk, delta_seconds=0)
    game = Game(game_dict)

    at_bat_lists = game.liveData.plays.allPlays

    isTopInning: bool = True
    inning: int = 0
    runners: List[bool] = [False, False, False] # [First, Second, Third]

    home_favor: float = float(0) # >0 = home helped, away hurt

    for ab in at_bat_lists:
        if (isTopInning != ab.about.isTopInning) or (inning != ab.about.inning):
            isTopInning = bool(ab.about.isTopInning)
            inning = int(ab.about.inning)
            runners = [False, False, False]

        for i in ab.pitchIndex:
            pitch: get.game.PlayEvents = ab.playEvents[i]

            home_favor_delta = pitch.calculate_delta_home_favor_zone_num(runners, isTopInning, moe=0)
            home_favor += home_favor_delta

            if home_favor_delta != 0 and print_every_missed_call is True:
                print(_missed_pitch_details(ab, pitch, runners, home_favor_delta))

        if ab.matchup.postOnFirst is not None:
            runners[0] = True
        else:
            runners[0] = False

        if ab.matchup.postOnSecond is not None:
            runners[1] = True
        else:
            runners[1] = False

        if ab.matchup.postOnThird is not None:
            runners[2] = True
        else:
            runners[2] = False

    return home_favor

def print_last_pitch(gamePk=None, delta_seconds=0):
    stdscr = curses.initscr()

    if gamePk is None:
        raise ValueError('gamePk not provided')
    
    spaces = '                                                                                                                        '
    game = Game(_get_game_dict(gamePk, delta_seconds=delta_seconds))

    isTopInning = True
    inning = 0
    runners = [False, False, False]

    home_favor = 0

    ab = game.liveData.plays.allPlays[-1]
    if inning != ab.about.inning or isTopInning != ab.about.isTopInning:
        isTopInning = ab.about.isTopInning
        inning = ab.about.inning
        runners = [False, False, False]

        if len(ab.playEvents) > 0:
            pitch = ab.playEvents[-1]
            home_delta = pitch.calculate_delta_home_favor_monte_carlo(runners, isTopInning)
            home_favor += home_delta

            stdscr.addstr(0, 0, f'{game.gameData.teams.away.teamName} ({ab.result.awayScore}) at {game.gameData.teams.home.teamName} ({ab.result.homeScore}) {spaces}')
            stdscr.addstr(1, 0, f'{ab.about.halfInning.capitalize()} {ab.about.inning} {spaces}')
            stdscr.addstr(2, 0, f'{pitch.count.balls}-{pitch.count.strikes} | {pitch.count.outs} Outs {spaces}')
            stdscr.addstr(3, 0, f'{ab.matchup.pitcher.fullName} to {ab.matchup.batter.fullName} {spaces}')
            stdscr.addstr(4, 0, f'Expected Runs: {get.game.PlayEvents.renp[pitch.count.balls][pitch.count.strikes][pitch.count.outs][get.game.PlayEvents._get_runners_int(runners)]}')
            
            try:
                if pitch.isPitch is True:
                    stdscr.addstr(6, 0, f'Pitch Details: {spaces}')
                    stdscr.addstr(7, 0, f'{pitch.details.description} {spaces}')
                    stdscr.addstr(8, 0, f'{pitch.pitchData.startSpeed} {pitch.details.type.description} {spaces}')
                    stdscr.addstr(9, 0, f'{pitch.pitchData.breaks.spinRate} RPM {spaces}')
                    stdscr.addstr(10, 0, f'{pitch.pitch_in_the_zone_str()} {spaces}')
                    stdscr.addstr(11, 0, f'{umpire(gamePk):.3f} [{home_delta:.3f}] {spaces}')
                else:
                    stdscr.addstr(6, 0, f'{spaces}')
                    stdscr.addstr(7, 0, f'{spaces}')
                    stdscr.addstr(8, 0, f'{spaces}')
                    stdscr.addstr(9, 0, f'{spaces}')
                    stdscr.addstr(10, 0, f'{spaces}')
                    stdscr.addstr(11, 0, f'{spaces}')

                if pitch.hitData is not None:
                    stdscr.addstr(13, 0, f'Hit Details: {spaces}')
                    stdscr.addstr(14, 0, f'Exit Velo: {pitch.hitData.launchSpeed} {spaces}')
                    stdscr.addstr(15, 0, f'Launch Angle: {pitch.hitData.launchAngle} {spaces}')
                    stdscr.addstr(16, 0, f'Total Dist: {pitch.hitData.totalDistance} {spaces}')
                else:
                    stdscr.addstr(13, 0, f'{spaces}')
                    stdscr.addstr(14, 0, f'{spaces}')
                    stdscr.addstr(15, 0, f'{spaces}')
                    stdscr.addstr(16, 0, f'{spaces}')
            except AttributeError:
                pass

            stdscr.refresh()
            time.sleep(.2)

        if ab.matchup.postOnFirst is not None:
            runners[0] = True
        else:
            runners[0] = False

        if ab.matchup.postOnSecond is not None:
            runners[1] = True
        else:
            runners[1] = False

        if ab.matchup.postOnThird is not None:
            runners[2] = True
        else:
            runners[2] = False

def print_every_pitch(gamePk=None):
    stdscr = curses.initscr()

    if gamePk is None:
        raise ValueError('gamePk not provided')
    
    spaces = '                                        '
    game = Game(_get_game_dict(gamePk))

    isTopInning = True
    inning = 0
    runners = [False, False, False]

    home_favor = 0

    for ab in game.liveData.plays.allPlays:
        if inning != ab.about.inning or isTopInning != ab.about.isTopInning:
            isTopInning = ab.about.isTopInning
            inning = ab.about.inning
            runners = [False, False, False]

        if len(ab.playEvents) > 0:
            for pitch in ab.playEvents:
                home_delta = pitch.calculate_delta_home_favor_zone_num(runners, isTopInning)
                home_favor += home_delta

                stdscr.addstr(0, 0, f'{game.gameData.teams.away.teamName} ({ab.result.awayScore}) at {game.gameData.teams.home.teamName} ({ab.result.homeScore}) {spaces}')
                stdscr.addstr(1, 0, f'{ab.about.halfInning.capitalize()} {ab.about.inning} {spaces}')
                stdscr.addstr(2, 0, f'{pitch.count.balls}-{pitch.count.strikes} | {pitch.count.outs} Outs {spaces}')
                stdscr.addstr(3, 0, f'{ab.matchup.pitcher.fullName} to {ab.matchup.batter.fullName} {spaces}')
                stdscr.addstr(4, 0, f'Expected Runs: {get.game.PlayEvents.renp[pitch.count.balls][pitch.count.strikes][pitch.count.outs][get.game.PlayEvents._get_runners_int(runners)]}')
                
                try:
                    if pitch.isPitch is True:
                        stdscr.addstr(6, 0, f'Pitch Details: {spaces}')
                        stdscr.addstr(7, 0, f'{pitch.details.description} {spaces}')
                        stdscr.addstr(8, 0, f'{pitch.pitchData.startSpeed} {pitch.details.type.description} {spaces}')
                        stdscr.addstr(9, 0, f'{pitch.pitchData.breaks.spinRate} RPM {spaces}')
                        stdscr.addstr(10, 0, f'{pitch.pitch_in_the_zone_str()} {spaces}')
                        stdscr.addstr(11, 0, f'{home_favor:.3f} [{home_delta:.3f}] {spaces}')
                    else:
                        stdscr.addstr(6, 0, f'{spaces}')
                        stdscr.addstr(7, 0, f'{spaces}')
                        stdscr.addstr(8, 0, f'{spaces}')
                        stdscr.addstr(9, 0, f'{spaces}')
                        stdscr.addstr(10, 0, f'{spaces}')
                        stdscr.addstr(11, 0, f'{spaces}')

                    if pitch.hitData is not None:
                        stdscr.addstr(13, 0, f'Hit Details: {spaces}')
                        stdscr.addstr(14, 0, f'Exit Velo: {pitch.hitData.launchSpeed} {spaces}')
                        stdscr.addstr(15, 0, f'Launch Angle: {pitch.hitData.launchAngle} {spaces}')
                        stdscr.addstr(16, 0, f'Total Dist: {pitch.hitData.totalDistance} {spaces}')
                    else:
                        stdscr.addstr(13, 0, f'{spaces}')
                        stdscr.addstr(14, 0, f'{spaces}')
                        stdscr.addstr(15, 0, f'{spaces}')
                        stdscr.addstr(16, 0, f'{spaces}')
                except AttributeError:
                    pass

                stdscr.refresh()

        if ab.matchup.postOnFirst is not None:
            runners[0] = True
        else:
            runners[0] = False

        if ab.matchup.postOnSecond is not None:
            runners[1] = True
        else:
            runners[1] = False

        if ab.matchup.postOnThird is not None:
            runners[2] = True
        else:
            runners[2] = False

if __name__ == '__main__':
    home_favor = umpire(717421, print_every_missed_call=True)
    print()
    print(f'{home_favor:>6.3f}')

    #while True:
    #    print_every_pitch(717421)
