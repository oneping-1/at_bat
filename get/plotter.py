"""
Module that prints pitch location similar to what Ump Scorecards has
Might get moved into umpire module in future if it makes more since
"""

from typing import List
from matplotlib import pyplot as plt
from matplotlib import patches
from .game import PlayEvents

class Plotter:
    def __init__(self):
        self.plate_width_inches = 17
        self.sX_min: float = -self.plate_width_inches/2/12
        self.sX_max: float = self.plate_width_inches/2/12

        # default top and bottom strike zone
        self.sZ_top: float = 3.5
        self.sZ_bot: float = 1.5
        self.zone_height = self.sZ_top - self.sZ_bot

        self.ball_radius_inches = 1.437

        self.axis = None


    def plot(self, pitches: List[PlayEvents]):
        if len(pitches) == 0:
            raise ValueError('len of pitches should be >1')
        if len(pitches) == 1:
            self.sZ_top = pitches[0].pitchData.coordinates.sZ_top
            self.sZ_bot = pitches[0].pitchData.coordinates.sZ_bot
            self.zone_height = self.sZ_top - self.sZ_bot

        _, self.axis = plt.subplots()

        zone = patches.Rectangle((self.sX_min, self.sZ_bot),
                                 width=self.plate_width_inches/12,
                                 height=self.zone_height,
                                 facecolor='none',
                                 edgecolor='black')

        self.axis.add_patch(zone)

        self._print_pitches(pitches)

        plt.xlim(-2, 2)
        plt.ylim(0,5)
        plt.xticks([])
        plt.yticks([])
        self.axis.set_aspect('equal')

        for spine in self.axis.spines.values():
            spine.set_visible(False)

        plt.show()

    def _print_pitches(self, pitches: List[PlayEvents]):
        for _, pitch in enumerate(pitches):
            pX = pitch.pitchData.coordinates.pX
            pZ = pitch.pitchData.coordinates.pZ

            code = pitch.details.code

            if code == 'C':
                color = 'red'
            elif code == 'B':
                color = 'green'

            pitch = patches.Circle((pX, pZ), radius=self.ball_radius_inches/12,
                                       facecolor='none', edgecolor=color)
            self.axis.add_patch(pitch)
            #self.axis.text(pX, pZ, str(i+1), ha='center', va='center')
