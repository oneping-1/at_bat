import curses
import time
import sys
from get.game import Game
import get
from get.statsapi_plus import get_runners_int, get_game_dict
from umpire_scorecard import umpire

def print_last_pitch(gamePk=None, delay_seconds=0):
    """
    Repetitively prints details for the last pitch and ball in play including:
    
    1. Away/Home teams + score
    2. Inning
    3. Count
    4. Pitcher and Batter name

    Pitch Details:
    5. Pitch Result
    6. Pitch Speed + Name
    7. Spin Rate
    8. If pitch was in zone + home favor if missed call

    Hit Details:
    9. Exit Velocity
    10. Launch Angle
    11. Total Distance

    FINISH DOC STRING
    """
    stdscr = curses.initscr()

    if gamePk is None:
        raise ValueError('gamePk not provided')

    spaces = ''
    spaces = ' ' * 50
    runners = [False, False, False]

    while True:
        try:
            game = Game(get_game_dict(gamePk, delay_seconds=delay_seconds))
            home_favor = 0

            at_bat = game.liveData.plays.allPlays[-1]

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

            runners_int = get_runners_int(runners)

            if len(at_bat.playEvents) > 0:
                pitch = at_bat.playEvents[-1]
                home_delta = pitch.get_delta_home_favor_monte_carlo(runners, at_bat.about.halfInning)
                home_favor += home_delta

                stdscr.addstr(0, 0, f'{game.gameData.teams.away.teamName} ({at_bat.result.awayScore}) at {game.gameData.teams.home.teamName} ({at_bat.result.homeScore}) {spaces}')
                stdscr.addstr(1, 0, f'{at_bat.about.halfInning.capitalize()} {at_bat.about.inning} - {runners} {spaces}')
                stdscr.addstr(2, 0, f'{pitch.count.balls}-{pitch.count.strikes} | {pitch.count.outs} Outs {spaces}')
                stdscr.addstr(3, 0, f'{at_bat.matchup.pitcher.fullName} to {at_bat.matchup.batter.fullName} {spaces}')
                stdscr.addstr(4, 0, f'Expected Runs: {get.game.PlayEvents.renp[pitch.count.balls][pitch.count.strikes][pitch.count.outs][runners_int]:.2f}')


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


                stdscr.refresh()
                time.sleep(.2)

        except KeyboardInterrupt:
            sys.exit()
        except AttributeError:
            pass

if __name__ == '__main__':
    #gamePk = input('Input gamePk: ')
    print_last_pitch(717405, delay_seconds=54)
