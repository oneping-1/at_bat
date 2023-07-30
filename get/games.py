"""
Handles logic to make a out-of-town like scoreboard for MLB games.
Useful to keep track of all games going on with the ability add a
delay to avoid spoilers

Classes:
    Games: Represents all games in a day in a single place

"""

from typing import List, Tuple
import curses
from tqdm import tqdm
from get.game import Game
from get.runners import Runners
from get.statsapi_plus import get_daily_gamePks


class Games:
    """
    Holds info for all games in a day. Held in a list so it's easily
    itterable. Can be printed using the curses library using the
    print_game() method

    Arguments:
        delay_seconds(int): The number of seconds the scoreboard should
            be delayed by. Useful when watching games live and do not
            want to get spoiled

    Attributes:
        gamePks (List[int]): A list of the gamePks for that days slate
            of games. The games list is then created using this list
        games (List[Game]): A list of the GameScoreboard class
            that holds info that would be required for a scoreboard

    Methods:
        update(): Updates the game data for each game in the games
            instance variable. Required so that scores can be updated
            throughout the night
        print_games(): A loop that will keep printing the scores to
            the console via the curses library. The loop will only break
            if ctrl+c is commanded
    """
    def __init__(self, delay_seconds: int = 0):
        self._delay_seconds = delay_seconds

        self.games: List[Game] = []
        self.gamePks = get_daily_gamePks()

        for gamePk in tqdm(self.gamePks):
            game = Game.get_game_from_pk(gamePk, self._delay_seconds)
            self.games.append(game)

    def update(self):
        """
        Updates the list of GameScoreboards so that the scoreboard can
        get the most recent info.
        """
        self.games: List[Game] = []
        for gamePk in tqdm(self.gamePks):
            game = Game.get_game_from_pk(gamePk, self._delay_seconds)
            self.games.append(game)

    def scoreboard(self):
        """
        Continuously prints scores for all games live in the format of
        a out-of-town scoreboard.

        Raises:
            _curses.error: If window size is not big enough. Enlarge the
                window to fix, needs to be fairly tall to fit all scores
        """
        stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        stdscr.clear()

        while True:

            line = 1
            for game in self.games:
                away_color, home_color = self._get_colors(game)
                away_line, home_line = self._get_text(game)

                curses.init_pair(line, away_color, 0)
                stdscr.addstr(line, 0, away_line, curses.color_pair(line))
                line += 1

                curses.init_pair(line, home_color, 0)
                stdscr.addstr(line, 0, home_line, curses.color_pair(line))
                line += 2

            stdscr.refresh()
            self.update()

    def _get_text(self, game: Game) -> Tuple[str, str]:
        away_team = game.gameData.teams.away.abbreviation
        home_team = game.gameData.teams.home.abbreviation

        away_score = game.liveData.linescore.teams.away.runs
        home_score = game.liveData.linescore.teams.home.runs

        start_time = game.gameData.datetime.startTime

        coded_game_state = game.gameData.status.codedGameState
        detailed_state = game.gameData.status.detailedState
        #abstract_state = game.gameData.status.abstractGameState

        inning_state = game.liveData.linescore.inningState
        inning = game.liveData.linescore.currentInning
        outs = game.liveData.linescore.outs

        runners = Runners()
        runners.set_bases_offense(game.liveData.linescore.offense)

        line_0 = f'{away_team:3s}  '
        line_1 = f'{home_team:3s}  '

        # Pregame
        if coded_game_state == 'P':
            line_0 += f'  {start_time}'
            return (line_0, line_1)

        # Scores
        line_0 += f'{away_score:2d} '
        line_1 += f'{home_score:2d} '

        # Final
        if coded_game_state == 'F':
            line_0 += ' F'
            if inning != 9:
                line_1 += f'{inning:2d}'
            return (line_0, line_1)

        # Top/Bottom of inning
        #if inning_state in ('Top', 'Middle'):
        #    line_0 += '= '
        #    line_1 += '  '
        #elif inning_state in ('Bottom', 'End'):
        #    line_0 += '  '
        #    line_1 += '= '

        # Delay
        if detailed_state in 'Delay':
            line_0 += ' D'
            line_1 += f'{game.inning:2d}'
            return (line_0, line_1)

        # Suspended
        if detailed_state in 'Suspended':
            line_0 += ' S'
            line_1 += f'{game.inning:2d}'
            return (line_0, line_1)

        # Live
        line_0 += f'o{outs} {repr(runners)}'
        line_1 += f'{inning:2d}'

        return (line_0, line_1)

    def _get_colors(self, game: Game):
        """
        0: Black/Dark Grey
        1: Darker Blue
        2: Green
        3: Lighter Blue
        4: Red
        5: Pink
        6: Yellow
        7: White
        (At least for me)
        ...
        """
        away_team = game.gameData.teams.away.abbreviation
        home_team = game.gameData.teams.home.abbreviation

        away_div = game.gameData.teams.away.division
        home_div = game.gameData.teams.home.division

        detailed_state = game.gameData.status.detailedState
        coded_game_state = game.gameData.status.codedGameState

        if coded_game_state in ('P', 'F'):
            away_color = 0
            home_color = 0

        if detailed_state in ('Warmup', 'Suspended'):
            away_color = 0
            home_color = 0

        if away_div == 'AW':
            away_color = 4

        if home_div == 'AW':
            home_color = 4

        if away_team == 'TEX':
            away_color = 1

        if home_team == 'TEX':
            home_color = 1

        bet_teams = ()
        if away_team in bet_teams:
            away_color = 2

        if home_team in bet_teams:
            home_color = 2

        return (away_color, home_color)

if __name__ == '__main__':
    scoreboard = Games()
    scoreboard.scoreboard()
