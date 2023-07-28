# pylint: disable=C0103, C0111
# pylint: disable=protected-access

import math
import csv
import pytest
import os
from get.game import PlayEvents
from get.runners import Runners
from get.umpire import Umpire

# https://community.fangraphs.com/the-effect-of-umpires-on-baseball-umpire-runs-created-urc/

def str_to_bool(string: str) -> bool:
    if string.lower() == 'false':
        return False
    if string.lower() == 'true':
        return True
    return None

def load_data_one_miss_games():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(csv_dir, 'one_miss_games.csv')

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        test_data = list(reader)
    return test_data


@pytest.mark.parametrize('test_data', load_data_one_miss_games())
def test_one_miss_games(test_data):
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
    home_delta_zone = Umpire.delta_favor_zone(pitch, int(runners), isTopInning)
    #home_delta_monte = Umpire.delta_favor_monte(pitch, int(runners), isTopInning)
    home_delta_dist = Umpire.delta_favor_dist(pitch, int(runners), isTopInning)

    delta_zone = float(test_data['delta_zone'])
    delta_monte = float(test_data['delta_monte'])

    assert home_delta_zone == pytest.approx(delta_zone, abs=1e-3)
    #assert home_delta_monte == pytest.approx(delta_monte, abs=1e-3)
    assert home_delta_dist == pytest.approx(delta_monte, abs=1e-3)


def load_data_random_moe():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(csv_dir, 'random_moe.csv')

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        test_data = list(reader)
    return test_data


@pytest.mark.parametrize('test_data', load_data_random_moe())
def test_random_moe(test_data):
    print(test_data['pX'])
    playEvents = {
        'pitchData': {
            'coordinates': {
                'pX': test_data['pX'],
                'pZ': test_data['pZ']
            },
            'strikeZoneTop': test_data['strikeZoneTop'],
            'strikeZoneBottom': test_data['strikeZoneBottom']
        }
    }

    pitch = PlayEvents(playEvents)

    # test pitch locations are added properly
    pX = pitch.pitchData.coordinates.pX
    pZ = pitch.pitchData.coordinates.pZ

    rand_x, rand_z = Umpire._generage_random_pitch_location(pitch)

    dx = math.pow(pX - rand_x, 2)
    dz = math.pow(pZ - rand_z, 2)
    mag = math.sqrt(dx + dz)

    assert mag <= Umpire.MOE
