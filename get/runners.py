from typing import List
from .game import AllPlays

class Runners:
    def __init__(self, runners: List[bool] = None):
        if runners is None:
            self.runners = [False, False, False]
        else:
            self.runners = runners

    def place_runners(self, at_bat: AllPlays):
        """
        Sets the runners based of the current at bat
        
        Args:
            at_bat: (get.game.AllPlays): The current at bat
        """
        if at_bat.matchup.postOnFirst is not None:
            self.runners[0] = True
        else:
            self.runners[0] = False

        if at_bat.matchup.postOnSecond is not None:
            self.runners[1] = True
        else:
            self.runners[1] = False

        if at_bat.matchup.postOnThird is not None:
            self.runners[2] = True
        else:
            self.runners[2] = False

    def clear_bases(self):
        """
        Manually clear the bases
        Can be used for a new half inning
        """
        self.runners = [False, False, False].copy()

    def __int__(self):
        i = 0

        if self.runners[0] is True:
            i += 1
        if self.runners[1] is True:
            i += 2
        if self.runners[2] is True:
            i += 4

        return i

    def __str__(self):
        if self.runners == [False, False, False]:
            return 'bases empty'
        elif self.runners == [True, False, False]:
            return 'runner on first'
        elif self.runners == [False, True, False]:
            return 'runner on second'
        elif self.runners == [True, True, False]:
            return 'runners on first and second'
        elif self.runners == [False, False, True]:
            return 'runner on third'
        elif self.runners == [True, False, True]:
            return 'runners on first and third'
        elif self.runners == [False, True, True]:
            return 'runners on second and third'
        elif self.runners == [True, True, True]:
            return 'bases loaded'
