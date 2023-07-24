"""
Module that has pitch info on pitches that show up on my missed call
calculation and what show up on Ump Scorecards Twitter in an attempt
to find trend
"""


from get.plotter import Plotter
from get.game import PlayEvents

pitch_01 = {
    # test_calculate_delta_04
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

# test_calculate_delta_06
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

# test_calculate_delta_13
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

# test_calculate_delta_17
pitch_04 = {
    'details': {
        'code': 'C'
    },
    'pitchData': {
        'strikeZoneTop': 3.47,
        'strikeZoneBottom': 1.72,
        'coordinates': {
            'pX': 0.61,
            'pZ': 1.55
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
