"""
Module that has pitch info on pitches that show up on my missed call
calculation and what show up on Ump Scorecards Twitter in an attempt
to find trend
"""


from get.plotter import Plotter
from get.game import PlayEvents

pitch_01 = {
    'details': {
        'code': 'B'
    },
    'pitchData': {
        'strikeZoneTop': 3.28,
        'strikeZoneBottom': 1.47,
        'coordinates': {
            'pX': 0.46,
            'pZ': 3.38
        }
    }
}

pitch_02 = {
    'details': {
        'code': 'C'
    },
    'pitchData': {
        'strikeZoneTop': 3.37,
        'strikeZoneBottom': 1.63,
        'coordinates': {
            'pX': 0.27,
            'pZ': 3.52
        }
    }
}

pitch_03 = {
    'details': {
        'code': 'B'
    },
    'pitchData': {
        'strikeZoneTop': 3.08,
        'strikeZoneBottom': 1.46,
        'coordinates': {
            'pX': -0.8,
            'pZ': 1.43
        }
    }
}

pitch_04 = {
    'details': {
        'code': 'C'
    },
    'pitchData': {
        'strikeZoneTop': 3.54,
        'strikeZoneBottom': 1.79,
        'coordinates': {
            'pX': -0.86,
            'pZ': 2.27
        }
    }
}

pitches = []
pitches.append(PlayEvents(pitch_01))
pitches.append(PlayEvents(pitch_02))
pitches.append(PlayEvents(pitch_03))
pitches.append(PlayEvents(pitch_04))

plotter = Plotter()
plotter.plot(pitches)
