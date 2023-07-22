"""
Module to unittest the plotter.py module. Has various scinerios to test
the methods in the Plotter class
"""

# pylint: disable=protected-access

from get.plotter import Plotter
from get.game import PlayEvents

def test_normalized_pitch_location_01():
    """
    One pitch, strike
    """
    pitch_dict_1 = {
        'details': {
            'code': 'C'
        },
        'pitchData': {
            'strikeZoneTop': 3.4,
            'strikeZoneBottom': 1.4,
            'coordinates': {
                'pX': 0,
                'pZ': 2
            }
        }
    }

    pitch_1 = PlayEvents(pitch_dict_1)

    plotter = Plotter()
    plotter.plot([pitch_1], False)

    pX_1, pZ_1, color_1 = plotter._get_normalized_pitch_location(pitch=pitch_1)

    assert pX_1 == 0
    assert pZ_1 == 2
    assert color_1 == 'red'


def test_normalized_pitch_location_02():
    """
    One pitch, strike
    """
    pitch_dict_1 = {
        'details': {
            'code': 'C'
        },
        'pitchData': {
            'strikeZoneTop': 3.55,
            'strikeZoneBottom': 1.39,
            'coordinates': {
                'pX': .35,
                'pZ': 1.35
            }
        }
    }

    pitch_1 = PlayEvents(pitch_dict_1)

    plotter = Plotter()
    plotter.plot([pitch_1], False)

    pX_1, pZ_1, color_1 = plotter._get_normalized_pitch_location(pitch=pitch_1)

    assert pX_1 == .35
    assert pZ_1 == 1.35
    assert color_1 == 'red'


def test_normalized_pitch_location_03():
    """
    Two pitches, both balls
    """
    pitch_dict_1 = {
        'details': {
            'code': 'B'
        },
        'pitchData': {
            'strikeZoneTop': 3.62,
            'strikeZoneBottom': 1.86,
            'coordinates': {
                'pX': 0.20,
                'pZ': 3.71
            }
        }
    }

    pitch_dict_2 = {
        'details': {
            'code': 'B'
        },
        'pitchData': {
            'strikeZoneTop': 3.52,
            'strikeZoneBottom': 1.55,
            'coordinates': {
                'pX': 0.83,
                'pZ': 2.70
            }
        }
    }

    pitch_1 = PlayEvents(pitch_dict_1)
    pitch_2 = PlayEvents(pitch_dict_2)

    plotter = Plotter()
    plotter.plot([pitch_1, pitch_2], False)

    pX_1, pZ_1, color_1 = plotter._get_normalized_pitch_location(pitch=pitch_1)
    pX_2, pZ_2, color_2 = plotter._get_normalized_pitch_location(pitch=pitch_2)

    assert pX_1 == 0.2
    assert pZ_1 == 3.59
    assert color_1 == 'green'

    assert pX_2 == 0.83
    assert pZ_2 == 2.68
    assert color_2 == 'green'
