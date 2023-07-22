"""
Module that prints a list of pitches' location using matplotlib library.
The plotter method takes in a list of get.Game.PlayEvents. The
PlayEvents class represents pitches in a game. 

Example:
from get.plotter import Plotter
plotter = Plotter()
plotter.plot([GameEvents])
"""

from typing import List
from matplotlib import pyplot as plt
from matplotlib import patches
from get.game import PlayEvents

class Plotter:
    """
    Plots the pitch using matplotlib. Main method is Plotter.plot()
    which does most of the heavy lifting
    """
    PLATE_WIDTH_INCHES = 17
    PLATE_WIDTH_FEET = PLATE_WIDTH_INCHES / 12
    sX_min: float = -PLATE_WIDTH_FEET / 2
    sX_max: float = PLATE_WIDTH_FEET / 2
    BALL_RADIUS_INCHES = 1.437
    BALL_RADIUS_FEET = BALL_RADIUS_INCHES / 12

    def __init__(self):
        # default top and bottom strike zone
        self.sZ_top: float = 3.5
        self.sZ_bot: float = 1.5
        self.zone_height = self.sZ_top - self.sZ_bot

        self.axis = None


    def plot(self, pitches: List[PlayEvents]):
        """
        Plots a list of pitches using matplot lib. Input is a list of
        pitches so that multiple pitches can be printed
        
        Arg:
            pitches (List[PlayEvents]): List of pitches
                (game.PlayEvents) that want to be plotted

        Raises:
            ValueError: If len(pitches) == 0
        """
        if len(pitches) == 0:
            raise ValueError('len of pitches should be >1')

        # normalized strike zone
        if len(pitches) == 1:
            self.sZ_top = pitches[0].pitchData.coordinates.sZ_top
            self.sZ_bot = pitches[0].pitchData.coordinates.sZ_bot
            self.zone_height = self.sZ_top - self.sZ_bot

        _, self.axis = plt.subplots()

        # creates strike zone box
        zone = patches.Rectangle((self.sX_min, self.sZ_bot),
                                 width=self.PLATE_WIDTH_FEET,
                                 height=self.zone_height,
                                 facecolor='none',
                                 edgecolor='black')

        # prints strike zone box
        self.axis.add_patch(zone)

        # creates and prints each pitch in list
        for _, pitch in enumerate(pitches):
            pX, pZ, color = self._get_normalized_pitch_location(pitch)
            pitch = patches.Circle((pX, pZ), radius=self.BALL_RADIUS_FEET,
                                    facecolor='none', edgecolor=color)
            self.axis.add_patch(pitch)
            #self.axis.text(pX, pZ, str(i+1), ha='center', va='center')

        plt.xlim(-2, 2)
        plt.ylim(0,5)
        plt.xticks([])
        plt.yticks([])
        self.axis.set_aspect('equal')

        for spine in self.axis.spines.values():
            spine.set_visible(False)

        plt.show()

    def _get_normalized_pitch_location(self, pitch: PlayEvents):
        pX = pitch.pitchData.coordinates.pX
        pZ = pitch.pitchData.coordinates.pZ

        code = pitch.details.code

        if code == 'C':
            color = 'red'
        elif code == 'B':
            color = 'green'
        else:
            color = 'black'

        # delta to top and bottom of strike zone
        d_top = pZ - pitch.pitchData.coordinates.sZ_top
        d_bot = pZ - pitch.pitchData.coordinates.sZ_bot

        # new pitch location accounted for normalized strike zone
        pZ_top = d_top + self.sZ_top
        pZ_bot = d_bot + self.sZ_bot

        if abs(pZ_top) > abs(pZ_bot):
            pZ = pZ_bot
        else:
            pZ = pZ_top

        return (pX, pZ, color)
