import csv
from datetime import datetime, timedelta
import statsapi
from colorama import Fore
import numpy as np

def get_game_dict(gamePk=None, delay_seconds=0) -> dict:
    """
    Returns the game dictionary for given game

    Essentially the same as statsapi.get('game') but with an extra
    function argument. This argument will let the dictionary returned
    to be from a given number of seconds ago. This is for when you are
    watching a game which is delayed to the data

    Args:
        gamePk (int): The gamePk/id for the desired game. Can easily
            be found on the MLB/MiLB websites
        delay_seconds (float, optional): The number of seconds the data
            should be delayed to match what you're seeing. Defaults to 0

    Returns:
        data (dict): The game dictionary recieved with the given delay.
            Can be turned into a Game object by using this dict as the
            only argument to Game. Example: 
            data = get_game_dict(717404, delay_seconds=45)
            game_class = Game(data)

    Raises:
        ValueError: If gamePk argument is not defined
        HTTPError: If gamePk argument is not valid
        TypeError: If delay_seconds is not valid 
    """
    if gamePk is None:
        raise ValueError('gamePk not provided')

    delay_time = get_utc_time(delay_seconds=delay_seconds)
    data = statsapi.get('game', {'gamePk': gamePk, 'timecode': delay_time}, force=True)
    return data

def get_utc_time(delay_seconds: int = 0):
    """
    returns the utc time in YYYMMDD-HHMMSS in 24 hour time

    Used for statsapi.get() functions that use time parameter
    'delay_seconds' can also be type float as well

    Args:
        delay_seconds (int, optional): Seconds behind present you want
        the output to be. Defaults to 0

    Returns:
        str: The UTC time in the 'YYYYMMDD-HHMMSS' format

    Raises:
        TypeError: If 'delay_seconds' is type str
    """
    # Get the current time in UTC
    utc_time = datetime.utcnow()

    # Subtract the delta
    utc_time = utc_time - timedelta(seconds=delay_seconds)

    # Format the time
    formatted_time = utc_time.strftime('%Y%m%d_%H%M%S')

    return formatted_time


def get_daily_gamePks(date: str = None):
    gamePks = []

    if date is not None:
        data = statsapi.schedule(date=date)
    elif date is None:
        data = statsapi.schedule()

    for game in data:
        gamePks.append(game['game_id'])

    return gamePks


def get_color_scoreboard(game):
    away = Fore.WHITE
    home = Fore.WHITE

    if 'Final' in game.gameData.status.abstractGameState or 'Preview' in game.gameData.status.abstractGameState or 'Warmup' in game.gameData.status.detailedState or 'Suspended' in game.gameData.status.detailedState:
        away = Fore.LIGHTBLACK_EX
        home = Fore.LIGHTBLACK_EX

    if game.gameData.teams.away.division == 'AW':
        away = Fore.LIGHTRED_EX

    if game.gameData.teams.home.division == 'AW':
        home = Fore.LIGHTRED_EX

    if game.gameData.teams.away.abbreviation == 'TEX':
        away = Fore.LIGHTBLUE_EX

    if game.gameData.teams.home.abbreviation == 'TEX':
        home = Fore.LIGHTBLUE_EX

    bet_teams = ('LAD', 'DET', 'MIN', 'TEX', 'LAA')
    if game.gameData.teams.away.abbreviation in bet_teams:
        away = Fore.LIGHTGREEN_EX

    if game.gameData.teams.home.abbreviation in bet_teams:
        home = Fore.LIGHTGREEN_EX

    return [away, home]


def get_color(team_abv:str, division:str):
    if team_abv == 'TEX':
        return Fore.LIGHTBLUE_EX
    elif division == 'AW':
        return Fore.LIGHTRED_EX
    else:
        return Fore.WHITE


def get_run_expectency_numpy() -> np.ndarray:
    """
    Returns the numpy array run expectency table

    Run expectency table obtained from:
    https://community.fangraphs.com/the-effect-of-umpires-on-baseball-umpire-runs-created-urc/

    How to index:
    renp[balls][strikes][outs][runners]
    where runners is a int obtained from get_runners_int() function

    Args:
        None
    
    Returns:
        numpy.ndarray: Run expectency table renp[balls][strikes][outs][runners]

    Raises:
        FileNotFoundError: re.csv file missing, renamed, or misplaced
    """
    renp = np.zeros((5,4,4,8))

    with open('csv/re.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            balls = int(row[0])
            strikes = int(row[1])
            outs = int(row[2])
            runners = int(row[3])
            run_expectency = float(row[4])

            renp[balls][strikes][outs][runners] = run_expectency

    return renp


if __name__ == '__main__':
    pass
