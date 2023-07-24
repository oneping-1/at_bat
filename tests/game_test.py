# pylint: disable=C0103, C0111
# pylint: disable=protected-access

import math
import csv
import pytest
from get.game import PlayEvents
from get.runners import Runners

# https://community.fangraphs.com/the-effect-of-umpires-on-baseball-umpire-runs-created-urc/

def load_data():
    with open('csv/test_calculate_delta.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        test_data = list(reader)
    return test_data

def str_to_bool(s: str):
    if s.lower() == 'true':
        return True
    if s.lower() == 'false':
        return False
    raise ValueError('argument is not True or False')


@pytest.mark.parametrize('test_data', load_data())
def test_calculate_delta(test_data):
    playEvents_dict = {
        'details': {
            'code': test_data['code']
        },
        'count': {
            'balls': int(test_data['balls']),
            'strikes': int(test_data['strikes']),
            'outs': int(test_data['outs'])
        },
        'pitchData': {
            'strikeZoneTop': float(test_data['strikeZoneTop']),
            'strikeZoneBottom': float(test_data['strikeZoneBottom']),
            'coordinates': {
                'pX': float(test_data['pX']),
                'pZ': float(test_data['pZ'])
            },
            'zone': int(test_data['zone'])
        }
    }

    runners = Runners()
    first = str_to_bool(test_data['first'])
    second = str_to_bool(test_data['second'])
    third = str_to_bool(test_data['third'])
    runners_list = [first, second, third]
    runners.set_bases(runners_list=runners_list)
    isTopInning = str_to_bool(test_data['isTopInning'])

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    delta_zone = float(test_data['delta_zone'])
    delta_monte = float(test_data['delta_monte'])
    assert home_delta_zone == pytest.approx(delta_zone, abs=1e-3)
    assert home_delta_monte == pytest.approx(delta_monte, abs=1e-3)

def test_random_moe_01():
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

def test_random_moe_02():
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

def test_random_moe_03():
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

def test_random_moe_04():
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

def test_random_moe_05():
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
