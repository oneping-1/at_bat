"""
Module that has pitch info on pitches that show up on my missed call
calculation and what show up on Ump Scorecards Twitter in an attempt
to find trend
"""


from get.plotter import Plotter
from get.game import PlayEvents

pitch_dict_1 = {
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

pitch_dict_2 = {
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

pitch_dict_3 = {
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

pitch_1 = PlayEvents(pitch_dict_1)
pitch_2 = PlayEvents(pitch_dict_2)
pitch_3 = PlayEvents(pitch_dict_3)

plotter = Plotter()
plotter.plot([pitch_1, pitch_2, pitch_3])
