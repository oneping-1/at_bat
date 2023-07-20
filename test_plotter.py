from get.plotter import Plotter
from get.game import PlayEvents

pitch_dict_1 = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 1,
            'strikes': 1,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.32,
            'strikeZoneBottom': 1.54,
            'coordinates': {
                'pX': 0.92,
                'pZ': 1.92
            },
            'zone': 14
        }
    }

pitch_dict_2 = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 4,
            'strikes': 1,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.28,
            'strikeZoneBottom': 1.47,
            'coordinates': {
                'pX': 0.46,
                'pZ': 3.38
            },
            'zone': 3
        }
    }

pitch_1 = PlayEvents(pitch_dict_1)
pitch_2 = PlayEvents(pitch_dict_2)

plotter = Plotter()
plotter.plot([pitch_1, pitch_2])
