from typing import List, Tuple
import curses
from get.game import Game
from get.runners import Runners
from get.statsapi_plus import get_daily_gamePks, get_game_dict


class Game_Scoreboard:
    def __init__(self, gamePk:int, delay_seconds: int = 0):
        self.gamePk: int = gamePk
        self._delay_seconds: int = delay_seconds
        self._game_dict: dict = get_game_dict(self.gamePk, delay_seconds)
        self.game = Game(self._game_dict)

        # gameData
        self.abstract_state = self.game.gameData.status.abstractGameState
        self.detailed_state = self.game.gameData.status.detailedState

        self.coded_game_state = self.game.gameData.status.codedGameState

        self.away_team = self.game.gameData.teams.away.abbreviation
        self.home_team = self.game.gameData.teams.home.abbreviation

        self._away_div = self.game.gameData.teams.away.division
        self._home_div = self.game.gameData.teams.home.division

        self.start_time = self.game.gameData.datetime.startTime

        # linescore
        self.away_score = self.game.liveData.linescore.teams.away.runs
        self.home_score = self.game.liveData.linescore.teams.home.runs

        self.outs = self.game.liveData.linescore.outs
        self._offense = self.game.liveData.linescore.offense
        self.runners: Runners = Runners()
        self.runners.set_bases_offense(self._offense)

        self.inning = self.game.liveData.linescore.currentInning
        self.inning_state = self.game.liveData.linescore.inningState

        # other
        self.away_color = 7
        self.home_color = 7

        self._get_colors()

    def __str__(self):
        ...

    def _get_colors(self):
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

        if self.abstract_state in ('Final', 'Preview'):
            self.away_color = 0
            self.home_color = 0

        if self.detailed_state in ('Warmup', 'Suspended'):
            self.away_color = 0
            self.home_color = 0

        if self._away_div == 'AW':
            self.away_color = 4

        if self._home_div == 'AW':
            self.home_color = 4

        if self.away_team == 'TEX':
            self.away_color = 1

        if self.home_team == 'TEX':
            self.home_color = 1

        bet_teams = ()
        if self.away_team in bet_teams:
            self.away_color = 2

        if self.home_team in bet_teams:
            self.home_color = 2


class Scoreboard:
    def __init__(self, delay_seconds: int = 0):
        self.games: List[Game_Scoreboard] = []
        gamePks = get_daily_gamePks()

        for gamePk in gamePks:
            self.games.append(Game_Scoreboard(gamePk, delay_seconds))

    def print_games(self):
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
                line_0, line_1 = self._get_text(game)

                curses.init_pair(line, game.away_color, 0)
                stdscr.addstr(line, 0, line_0, curses.color_pair(line))
                line += 1

                curses.init_pair(line, game.home_color, 0)
                stdscr.addstr(line, 0, line_1, curses.color_pair(line))
                line += 2

            stdscr.refresh()

    def _get_text(self, game: Game_Scoreboard) -> Tuple[str, str]:
        line_0 = f'{game.away_team:3s}'
        line_1 = f'{game.home_team:3s}'

        # Pregame
        if game.coded_game_state == 'P':
            line_0 += f'  {game.start_time}'
            return (line_0, line_1)

        if game.inning_state in ('Top', 'Middle'):
            line_0 += '= '
            line_1 += '  '
        elif game.inning_state in ('Bottom', 'End'):
            line_0 += '  '
            line_1 += '= '

        line_0 += f'{game.away_score:2d} '
        line_1 += f'{game.home_score:2d} '

        if game.detailed_state in 'Delay':
            line_0 += ' D'
            line_1 += f'{game.inning:2d}'
            return (line_0, line_1)

        if game.detailed_state in 'Suspended':
            line_0 += ' S'
            line_1 += f'{game.inning:2d}'
            return (line_0, line_1)

        if game.abstract_state in 'Final':
            line_0 += ' F'
            if game.inning != 9:
                line_1 += f'{game.inning:2d}'
            return (line_0, line_1)

        line_0 += f'o{game.outs} {repr(game.runners)}'
        line_1 += f'{game.inning:2d}'

        return (line_0, line_1)


if __name__ == '__main__':
    scoreboard = Scoreboard()
    scoreboard.print_games()
