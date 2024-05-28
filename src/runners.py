"""
This module provides the Runners class, which represents runners on the
base paths and which bases are occupied in a baseball game. The class
provides methods to manage the state of the bases through the course of
a game, automatically clearing the bases when a new half inning starts,
updating the bases after each at bat, manually clearing or setting the
bases, and providing string representations of the current state of the
bases.

Classes:
    Runners: Represents runners on the base paths and which bases
        are occupied in a game

Example:

    game = Game.get_game_from_pk(717239)
    runners = Runners()

    runners.set_bases_offenese(game.liveData.linescore.offense)
    # or
    runners.set_bases([True, False, False]) # set runners on first
"""

from typing import List
from src.game import AllPlays, Offense, RunnersMovement


class Runners:
    """
    Represents runners on the base paths and which bases are occupied

    Attributes:
        runners (List[bool]): A list of length 3 where each element
            represents if a runner is currently stood on the base or
            not. runners[0] is first base, runners[1] is second, and
            runners[2] is third.
        isTopInning (bool): Variable that describes if it is the top
            half of the inning. True if it is the top half, false if it
            is not
        inning (int): The current inning number
    """

    def __init__(self):
        """
        Initializes Runners class. Also holds inning info so that it
        can clear the bases automatically
        """
        self.runners = [False, False, False]
        self.isTopInning = None
        self.inning = 0

    def new_at_bat(self, at_bat: AllPlays):
        """
        Checks if a new half inning has started. If so, will clear the
        bases. This method should be run at the start of an at bat. If
        its not, then runners will not be cleared each half inning

        Args:
            at_bat (src.game.AllPlays): The current AllPlays (at bat)
                instance variable that holds the current half inning,
                and inning status
        """
        isTopInning = at_bat.about.isTopInning
        inning = at_bat.about.inning

        if (self.isTopInning != isTopInning or self.inning != inning) and inning > 9:
            # Extra innings
            # Worried if a 7 inning game that goes into extra innings
            # but should be fine for MLB
            self.isTopInning = isTopInning
            self.inning = inning
            self.runners = [False, True, False]
        elif self.isTopInning != isTopInning or self.inning != inning:
            self.isTopInning = isTopInning
            self.inning = inning
            self.clear_bases()

    def end_at_bat(self, at_bat: AllPlays):
        """
        Update class instance at the end of an at bat. Places the
        runners based off the outcome of the at bat.

        Args:
            at_bat (src.game.AllPlays): The current AllPlays (at bat)
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

    def set_bases_from_offense(self, offense: Offense):
        """
        Set the runners instance variable based off the Offense class
        in the game module. Can input the game.liveData.linescore.offense
        directly as a method argument and adjust the runners variable
        correctly

        Args:
            offense (Offense): The Offense class from src.game that
                holds live data on where the runners are on the base
                paths.
        """
        is_first = offense.is_first
        is_second = offense.is_second
        is_third = offense.is_third

        runners_list = [is_first, is_second, is_third]
        self.runners = runners_list.copy()

    def process_runner_movement(self, runner_movements: List[RunnersMovement], index: int):
        """
        Processes runner movements as you iterate through the pitches
        in a game. For this method to work properly, you must skip the
        last pitch of the at bat and use end_at_bat method to update the
        runners instead.

        This method works by checking if the current playIndex (pitch
        number from the at bat) matches any of the runner movement
        indexes. If it does, it will update the runners variable

        Args:
            runner_movements (List[Runners]): List of runners events
                during the at bat
            playIndex (int): Current playIndex number from the at bat

        Raises:
            ValueError: If a runner is moved away from a base and
                there is no runner on that base
            ValueError: If two runners are moved to the same base
        """
        runners_delta = [0, 0, 0]

        for i, runner in enumerate(self.runners):
            if runner is True:
                runners_delta[i] = 1

        for runner_movement in runner_movements:
            if index == runner_movement.details.playIndex:
                runner_delta_return = self._runner_movement(runner_movement)
                runners_delta = [a + b for a,b in zip(runners_delta, runner_delta_return)]

        for runner in runners_delta:
            if runner < 0:
                raise ValueError('Runner movement is negative')
            if runner > 1:
                raise ValueError('Runner movement is greater than 1')

        for i, runner in enumerate(runners_delta):
            if runner == 1:
                self.runners[i] = True

    def _runner_movement(self, runner_movement) -> List[int]:
        runner_delta = [0, 0, 0]

        if runner_movement.movement.start == '1B':
            runner_delta[0] += -1

        if runner_movement.movement.start == '2B':
            runner_delta[1] += -1

        if runner_movement.movement.start == '3B':
            runner_delta[2] += -1

        if runner_movement.movement.end == '1B' and runner_movement.movement.isOut is False:
            runner_delta[0] += 1

        if runner_movement.movement.end == '2B' and runner_movement.movement.isOut is False:
            # if self.runners[1] is True:
                # raise ValueError('Runner already on second base')
            self.runners[1] = True
            runner_delta[1] += 1

        if runner_movement.movement.end == '3B' and runner_movement.movement.isOut is False:
            runner_delta[2] += 1

        return runner_delta

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
