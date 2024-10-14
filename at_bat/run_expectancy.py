"""
This module contains the RunExpectancy class.
"""

class RunExpectancy:
    """
    A class to represent the run expectancy for a given situation
    """
    def __init__(self, total_runs: int, count: int, average_runs: float, runs1: int, runs2: int, runs3: int, runs4: int):
        self.total_runs = total_runs
        self.count = count
        self.average_runs = average_runs
        self.runs1 = runs1
        self.runs2 = runs2
        self.runs3 = runs3
        self.runs4 = runs4
