import os
import json
import copy
from datetime import datetime
import pytest
from at_bat.game import Game, _get_utc_time, KNOWN_GAMESTATES
import statsapi

# Language: python

# Relative import to bring in the Game class from game.py

@pytest.fixture
def sample_game_dict():
    # Build the path relative to this test file.
    test_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(test_dir, '..', 'examples', 'game.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip any comment lines that start with //
        lines = f.readlines()
        json_str = "".join(line for line in lines if not line.strip().startswith("//"))
        data = json.loads(json_str)
    return data

def test_game_instantiation(sample_game_dict):
    game = Game(sample_game_dict)
    # Check that gamePk is set correctly
    assert game.gamepk == sample_game_dict.get("gamePk")
    # Check that children are converted
    # game.gameData should have been converted; check for an attribute that GameData creates
    assert hasattr(game.gameData, "datetime")
    # liveData should be an instance with plays etc.
    assert hasattr(game.liveData, "plays")

def test_game_repr(sample_game_dict):
    game = Game(sample_game_dict)
    # __repr__ returns a string representation of game.gamepk
    assert repr(game) == str(sample_game_dict.get("gamePk"))

def test_game_equality(sample_game_dict):
    game1 = Game(sample_game_dict)
    # Make a deep copy to simulate a separate identical input
    game_dict_copy = copy.deepcopy(sample_game_dict)
    game2 = Game(game_dict_copy)
    assert game1 == game2

def fake_statsapi_get(endpoint, params, request_kwargs=None, force=False):
    # Return the same sample dict irrespective of input. This fakes the API call.
    test_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(test_dir, '..', 'examples', 'game.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        json_str = "".join(line for line in lines if not line.strip().startswith("//"))
        data = json.loads(json_str)
    return data

def test_get_game_from_pk(monkeypatch, sample_game_dict):
    # Monkeypatch statsapi.get in game module to return sample_game_dict
    monkeypatch.setattr(statsapi, "get", fake_statsapi_get)
    # Use a known gamePk from sample
    gamepk = sample_game_dict.get("gamePk")
    game = Game.get_game_from_pk(gamepk, delay_seconds=0)
    assert game.gamepk == gamepk

def test_children_conversion(sample_game_dict):
    game = Game(sample_game_dict)
    # Check that gameData.datetime is an instance of a class that has "officialDate"
    # Since our GameData replaces raw dicts with corresponding classes,
    # Check if the datetime attribute has an officialDate attribute.
    assert hasattr(game.gameData.datetime, "officialDate")
    # Check teams conversion: gameData.teams should have an "away" attribute with "abbreviation"
    assert hasattr(game.gameData.teams.away, "abbreviation")
    # Check liveData.linescore conversion: linescore should have attribute currentInningOrdinal
    assert hasattr(game.liveData.linescore, "currentInningOrdinal")

def test_utc_time_format():
    # Test _get_utc_time returns a string in the expected format YYYYMMDD_HHMMSS
    time_str = _get_utc_time(delay_seconds=0)
    try:
        dt = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
    except ValueError:
        pytest.fail("Returned UTC time string does not match expected format YYYYMMDD_HHMMSS")