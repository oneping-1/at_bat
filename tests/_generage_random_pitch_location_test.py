from get.game import PlayEvents
import math

def test_random_MOE_01():
    pX = 0
    pZ = 0

    playEvents = {
        'pitchData': {
            'coordinates': {
                'pX': pX,
                'pZ': pZ
            },
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5
        }
    }

    pitch = PlayEvents(playEvents)

    rand_x, rand_z = pitch._generage_random_pitch_location()

    dx = math.pow(pX - rand_x, 2)
    dz = math.pow(pZ - rand_z, 2)
    mag = math.sqrt(dx + dz)

    assert mag <= PlayEvents.MOE

def test_random_MOE_02():
    pX = 0
    pZ = 1

    playEvents = {
        'pitchData': {
            'coordinates': {
                'pX': pX,
                'pZ': pZ
            },
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5
        }
    }

    pitch = PlayEvents(playEvents)

    rand_x, rand_z = pitch._generage_random_pitch_location()

    dx = math.pow(pX - rand_x, 2)
    dz = math.pow(pZ - rand_z, 2)
    mag = math.sqrt(dx + dz)

    assert mag <= PlayEvents.MOE

def test_random_MOE_03():
    pX = 1
    pZ = 0

    playEvents = {
        'pitchData': {
            'coordinates': {
                'pX': pX,
                'pZ': pZ
            },
            'strikeZoneTop': 5,
            'strikeZoneBottom': 1
        }
    }

    pitch = PlayEvents(playEvents)

    rand_x, rand_z = pitch._generage_random_pitch_location()

    dx = math.pow(pX - rand_x, 2)
    dz = math.pow(pZ - rand_z, 2)
    mag = math.sqrt(dx + dz)

    assert mag <= PlayEvents.MOE

def test_random_MOE_04():
    pX = 0
    pZ = 2

    playEvents = {
        'pitchData': {
            'coordinates': {
                'pX': pX,
                'pZ': pZ
            },
            'strikeZoneTop': 2.5,
            'strikeZoneBottom': 2
        }
    }

    pitch = PlayEvents(playEvents)

    rand_x, rand_z = pitch._generage_random_pitch_location()

    dx = math.pow(pX - rand_x, 2)
    dz = math.pow(pZ - rand_z, 2)
    mag = math.sqrt(dx + dz)

    assert mag <= PlayEvents.MOE

def test_random_MOE_05():
    pX = -3
    pZ = 0

    playEvents = {
        'pitchData': {
            'coordinates': {
                'pX': pX,
                'pZ': pZ
            },
            'strikeZoneTop': 4,
            'strikeZoneBottom': 1
        }
    }

    pitch = PlayEvents(playEvents)

    rand_x, rand_z = pitch._generage_random_pitch_location()

    dx = math.pow(pX - rand_x, 2)
    dz = math.pow(pZ - rand_z, 2)
    mag = math.sqrt(dx + dz)

    assert mag <= PlayEvents.MOE