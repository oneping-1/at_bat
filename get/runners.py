"""
Module that holds the Runners class that is reposnible for keeping track
of which bases are occupied on the bases. Two public methods that need
to be run at the beginning and end of each at bat when itterating
through at bats in a game
"""

from typing import List
from get.game import AllPlays, Offense


class Runners:
    """
    Handles runners on base paths

    Attributes:
        runners (List[bool]): A list of length 3 where each element
            represents if a runner is currently stood on the base or
            not. runners[0] is first base, runners[1] is second, and
            runners[2] is third.
        isTopInning (bool): Variable that describes if it is the top
            half of the inning. True if it is the top half, false if it
            is not
        inning (int): The current inning number

    Methods:
        new_batter(at_bat: AllPlays): Checks if a new inning has started
            in the game module and clears bases if new half inning has
            started
        end_batter(at_bat: AllPlays): Sets Runners.runners based off the
            current position of the batters at the end of an at bat
        clear_bases(): Clears the bases of runners. Mainly used if a new
            half inning has started and want to manually clear bases
        set_bases(runners_list: List[bool]): Argument is a list of bools
            that indicate where runners are. Useful if want to manually
            set runner position on bases
        set_bases_offense(offense: Offense): Method to adjust runners
            instance variable automatically based off live runner
            locations in the game class
    """

    def __init__(self):
        """
        Initializes Runners class. Also holds inning info so that it
        can clear the bases automatically
        """
        self.runners = [False, False, False]
        self.isTopInning = None
        self.inning = 0

    def new_batter(self, at_bat: AllPlays):
        """
        Checks if a new half inning has started. If so, will clear the
        bases. This method should be run at the start of an at bat. If
        its not, then runners will not be cleared each half inning

        Args:
            at_bat (get.game.AllPlays): The current AllPlays (at bat)
                instance variable that holds the current half inning,
                and inning status
        """
        isTopInning = at_bat.about.isTopInning
        inning = at_bat.about.inning

        if self.isTopInning != isTopInning or self.inning != inning:
            self.isTopInning = isTopInning
            self.inning = inning
            self.runners = [False, False, False].copy()

    def end_batter(self, at_bat: AllPlays):
        """
        Update class instance at the end of an at bat. Places the
        runners based off the outcome of the at bat.

        Args:
            at_bat (get.game.AllPlays): The current AllPlays (at bat)
                instance variable that holds the runners location
                post at bat.
        """
        if at_bat.matchup.postOnFirst is None:
            self.runners[0] = False
        else:
            self.runners[0] = True

        if at_bat.matchup.postOnSecond is None:
            self.runners[1] = False
        else:
            self.runners[1] = True

        if at_bat.matchup.postOnThird is None:
            self.runners[2] = False
        else:
            self.runners[2] = True

    def clear_bases(self):
        """
        Manually clear the bases
        Can be used for a new half inning
        """
        self.runners = [False, False, False].copy()

    def set_bases(self, runners_list: List[bool]):
        """
        Manually set runners location on the bases

        Arguments:
            runners_list (List[bool]): List of runners locations with
                index 0 being first base and index 2 being third base.
                Switch each index to True if a runner is on the base
                and False if no runner is on the base

        Raises:
            ValueError: If len of runners_list is not 3
            TypeError: If elements in runners_list are not type bool
        """
        if len(runners_list) != 3:
            raise ValueError('runners_list is not len 3')

        for base in runners_list:
            if base is not False and base is not True:
                raise TypeError('Elements should be type bool')

        self.runners = runners_list.copy()

    def set_bases_offense(self, offense: Offense):
        """
        Set the runners instance variable based off the Offense class
        in the game module. Can input the game.liveData.linescore.offense
        directly as a method argument and adjust the runners variable
        correctly

        Args:
            offense (Offense): The Offense class from get.game that
                holds live data on where the runners are on the base
                paths.
        """
        is_first = offense.is_first
        is_second = offense.is_second
        is_third = offense.is_third

        runners_list = [is_first, is_second, is_third]
        self.runners = runners_list.copy()

    def __int__(self) -> int:
        """
        Converts the current state of the bases to an integer
        representation.

        Returns:
            int: The binary representation of the bases converted to an
                integer. The value will range from 0 (no runners on
                base) to 7 (bases loaded).
        """
        i = 0

        if self.runners[0] is True:
            i += 1
        if self.runners[1] is True:
            i += 2
        if self.runners[2] is True:
            i += 4

        return i

    def __str__(self) -> str:
        """
        Converts the current the current state of the bases into a
        readable sentence someone would say

        Returns:
            str: Readable sentence that represents the bases. 'bases
            empty', 'runner on first', 'bases loaded'
        """
        if self.runners == [False, False, False]:
            return 'bases empty'
        if self.runners == [True, False, False]:
            return 'runner on first'
        if self.runners == [False, True, False]:
            return 'runner on second'
        if self.runners == [True, True, False]:
            return 'runners on first and second'
        if self.runners == [False, False, True]:
            return 'runner on third'
        if self.runners == [True, False, True]:
            return 'runners on first and third'
        if self.runners == [False, True, True]:
            return 'runners on second and third'
        if self.runners == [True, True, True]:
            return 'bases loaded'

    def __repr__(self) -> str:
        """
        Converts the current state of bases into short string that
        quickly describes base status.

        Returns:
            str: Base status as short string. '___' for bases empty,
                '1__' for runner on first, '_23' for runner on second
                and third, '123' for bases loaded
        """
        code = ''

        for i, runner in enumerate(self.runners, start=1):
            if runner is True:
                code += str(i)
            else:
                code += '_'

        return code
