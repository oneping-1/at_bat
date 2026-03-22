import copy
import json
from datetime import datetime, timedelta

import pytest
import requests

from at_bat import game as game_module
from at_bat.game import (
    KNOWN_GAMESTATES,
    About,
    Count,
    Game,
    Movement,
    Offense,
    PitchCoordinates,
    PitchData,
    PlayEvents,
    Player,
    Status,
    _convert_zulu_to_local,
    _get_division,
    _get_utc_time,
    _get_utc_time_from_zulu,
)


@pytest.fixture
def sample_game_dict():
    with open('tests/test_json/748534.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def test_game_instantiation_builds_nested_types(sample_game_dict):
    game = Game(sample_game_dict)

    assert game.gamepk == sample_game_dict['gamePk']
    assert game.gameData.datetime.officialDate == sample_game_dict['gameData']['datetime']['officialDate']
    assert game.gameData.teams.away.abbreviation == sample_game_dict['gameData']['teams']['away']['abbreviation']
    assert len(game.liveData.plays.allPlays) == len(sample_game_dict['liveData']['plays']['allPlays'])


def test_game_repr_and_equality(sample_game_dict):
    game1 = Game(sample_game_dict)
    game2 = Game(copy.deepcopy(sample_game_dict))

    assert repr(game1) == str(sample_game_dict['gamePk'])
    assert game1 == game2


def test_get_game_from_pk_validates_input():
    with pytest.raises(ValueError, match='gamePk not provided'):
        Game.get_game_from_pk(None)


def test_get_game_from_pk_uses_iso_time(monkeypatch, sample_game_dict):
    calls = {}

    def fake_get_dict(cls, gamepk=None, iso_time=None, delay_seconds=0):
        calls['gamepk'] = gamepk
        calls['iso_time'] = iso_time
        calls['delay_seconds'] = delay_seconds
        return sample_game_dict

    monkeypatch.setattr(Game, 'get_dict', classmethod(fake_get_dict))

    game = Game.get_game_from_pk(748534, iso_time='2024-08-01T12:34:56Z')

    assert game.gamepk == 748534
    assert calls == {
        'gamepk': 748534,
        'iso_time': '2024-08-01T12:34:56Z',
        'delay_seconds': 0,
    }


def test_get_dict_retries_then_succeeds(monkeypatch, sample_game_dict):
    class FakeRequestException(requests.exceptions.RequestException):
        pass

    call_counter = {'count': 0}
    sleep_calls = []

    def fake_statsapi_get(*_args, **_kwargs):
        call_counter['count'] += 1
        if call_counter['count'] < 3:
            raise FakeRequestException('temporary network issue')
        return sample_game_dict

    monkeypatch.setattr(game_module.statsapi, 'get', fake_statsapi_get)
    monkeypatch.setattr(game_module, 'sleep', lambda seconds: sleep_calls.append(seconds))

    data = Game.get_dict(gamepk=748534, delay_seconds=0)

    assert data['gamePk'] == 748534
    assert call_counter['count'] == 3
    assert sleep_calls == [1, 2]


def test_get_dict_uses_iso_timecode(monkeypatch, sample_game_dict):
    captured = {}

    def fake_statsapi_get(endpoint, params, request_kwargs=None, force=False):
        captured['endpoint'] = endpoint
        captured['params'] = params
        captured['request_kwargs'] = request_kwargs
        captured['force'] = force
        return sample_game_dict

    monkeypatch.setattr(game_module.statsapi, 'get', fake_statsapi_get)

    Game.get_dict(gamepk=748534, iso_time='2024-10-05T01:02:03Z')

    assert captured['endpoint'] == 'game'
    assert captured['params']['gamePk'] == 748534
    assert captured['params']['timecode'] == '20241005_010203'
    assert captured['request_kwargs'] == {'timeout': 10}
    assert captured['force'] is True


def test_status_game_state_mappings_cover_core_paths():
    delayed = Status({'abstractGameState': 'Live', 'detailedState': 'Delayed', 'statusCode': 'IO', 'codedGameState': 'I'})
    suspended = Status({'abstractGameState': 'Live', 'detailedState': 'Suspended', 'statusCode': 'TR', 'codedGameState': 'I'})
    pre = Status({'abstractGameState': 'Preview', 'detailedState': 'Scheduled', 'statusCode': 'S', 'codedGameState': 'P'})
    live = Status({'abstractGameState': 'Live', 'detailedState': 'In Progress', 'statusCode': 'I', 'codedGameState': 'I'})
    final = Status({'abstractGameState': 'Final', 'detailedState': 'Final', 'statusCode': 'F', 'codedGameState': 'F'})
    cancelled = Status({'abstractGameState': 'Final', 'detailedState': 'Cancelled', 'statusCode': 'C', 'codedGameState': 'C'})
    unknown = Status({'abstractGameState': 'Unknown', 'detailedState': 'Unknown', 'statusCode': 'ZZ', 'codedGameState': 'Z'})

    assert delayed.game_state == 'D'
    assert suspended.game_state == 'S'
    assert pre.game_state == 'P'
    assert live.game_state == 'L'
    assert final.game_state == 'F'
    assert cancelled.game_state == 'C'
    assert unknown.game_state == 'U'


def test_known_gamestates_contains_expected_values():
    assert 'I' in KNOWN_GAMESTATES
    assert 'F' in KNOWN_GAMESTATES
    assert 'C' not in KNOWN_GAMESTATES


@pytest.mark.parametrize(
    ('code', 'division'),
    [
        ('NYY', 'AL East'),
        ('MIN', 'AL Central'),
        ('SEA', 'AL West'),
        ('NYM', 'NL East'),
        ('STL', 'NL Central'),
        ('LAD', 'NL West'),
        ('XXX', None),
    ],
)
def test_get_division(code, division):
    assert _get_division(code) == division


def test_get_utc_time_format_and_delay_window():
    delayed = _get_utc_time(delay_seconds=30)
    parsed = datetime.strptime(delayed, '%Y%m%d_%H%M%S')
    delta = datetime.utcnow() - parsed
    assert timedelta(seconds=25) <= delta <= timedelta(seconds=40)


def test_get_utc_time_from_zulu_formats_correctly():
    assert _get_utc_time_from_zulu('2024-07-04T11:22:33Z') == '20240704_112233'


def test_convert_zulu_to_local_handles_none():
    assert _convert_zulu_to_local(None) is None


def test_count_and_about_repr_and_conversion(sample_game_dict):
    first_play = sample_game_dict['liveData']['plays']['allPlays'][0]

    count = Count(first_play['count'])
    about = About(first_play['about'])

    assert isinstance(count.balls, int)
    assert isinstance(count.strikes, int)
    assert isinstance(count.outs, int)
    assert '-' in repr(count)
    assert about.isTopInning in (True, False)
    assert isinstance(about.inning, int)


def test_movement_base_number_calculations():
    movement = Movement({
        'originBase': '1B',
        'start': '2B',
        'end': 'score',
        'outBase': '3B',
        'isOut': False,
        'outNumber': None,
    })

    assert movement.originBaseNum == 1
    assert movement.startNum == 2
    assert movement.endNum == 4
    assert movement.outBaseNum == 3


def test_offense_runner_flags_and_player_conversion():
    offense = Offense({
        'batter': {'id': 1, 'fullName': 'A Batter', 'link': '/a'},
        'onDeck': {'id': 2, 'fullName': 'On Deck', 'link': '/b'},
        'inHole': {'id': 3, 'fullName': 'In Hole', 'link': '/c'},
        'first': {'id': 4, 'fullName': 'On First', 'link': '/d'},
        'second': None,
        'third': {'id': 5, 'fullName': 'On Third', 'link': '/e'},
        'pitcher': {'id': 6, 'fullName': 'Pitcher', 'link': '/f'},
        'battingOrder': 101,
    })

    assert offense.is_first is True
    assert offense.is_second is False
    assert offense.is_third is True
    assert isinstance(offense.batter, Player)
    assert offense.batter.fullName == 'A Batter'


def test_pitch_coordinates_validity_and_bounds():
    coords = PitchCoordinates({'pX': 0.1, 'pZ': 2.3}, sz_top=3.5, sz_bot=1.5)
    invalid = PitchCoordinates({'pX': None, 'pZ': 2.0}, sz_top=3.5, sz_bot=1.5)

    assert coords.is_valid() is True
    assert invalid.is_valid() is False
    assert coords.pX_min < coords.pX_max
    assert coords.pZ_min < coords.pZ_max


def test_pitch_data_and_playevents_repr_behavior():
    pitch_data = PitchData({
        'startSpeed': '95.4',
        'endSpeed': '87.1',
        'strikeZoneTop': 3.4,
        'strikeZoneBottom': 1.5,
        'coordinates': {'pX': 0.0, 'pZ': 2.1},
        'zone': '5',
        'plateTime': '0.4',
        'breaks': {'spinRate': 2400},
    })

    play_event = PlayEvents({
        'details': {'description': 'Called Strike', 'isPitch': True, 'type': {'code': 'FF', 'description': 'Four-Seam Fastball'}},
        'count': {'balls': 0, 'strikes': 1, 'outs': 0},
        'pitchData': {
            'startSpeed': 96,
            'endSpeed': 88,
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {'pX': 0.05, 'pZ': 2.2},
            'zone': 4,
        },
        'isPitch': True,
        'index': 1,
    })

    assert str(pitch_data) == 'In Zone'
    assert repr(play_event) == 'Called Strike'
    assert play_event == play_event
    assert play_event != None
