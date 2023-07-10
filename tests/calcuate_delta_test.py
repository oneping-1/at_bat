from ..get.game import PlayEvents
import pytest

def test_calculate_delta_01():
    """
    Strike called Strike
    Top of inning
    0-0 count
    """
    playEvents_dict = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 0,
            'strikes': 1,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': 0,
                'pZ': 2
            }
        }
    }

    runners = [False, False, False]
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == 0

def test_calculate_delta_02():
    """
    Ball called Ball
    Bottom of inning
    0-0 count
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 0,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': 2,
                'pZ': 4
            }
        }
    }

    runners = [False, False, False]
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == 0

def test_calculate_delta_03():
    """
    Strike called Ball
    Top of inning
    0-0 count

    How to calculate
    re_count[C2] - re_count[B3]
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 0,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': 0,
                'pZ': 2.5
            }
        }
    }

    runners = [False, False, False]
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(-.082, abs=1e-3)

def test_calculate_delta_04():
    """
    Strike called Ball
    Bottom of inning
    0-0 count

    How to calculate
    re_count[B3] - re_count[C2]
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 0,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': 0,
                'pZ': 2.5
            }
        }
    }

    runners = [False, False, False]
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(.082, abs=1e-3)

def test_calculate_delta_05():
    """
    Ball called Strike
    Top of inning
    0-0 count

    How to calculate
    re_count[C2] - re_count[B3]
    """
    playEvents_dict = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 0,
            'strikes': 1,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': 2,
                'pZ': 4
            }
        }
    }

    runners = [False, False, False]
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(.082, abs=1e-3)

def test_calculate_delta_06():
    """
    Ball called Strike
    Bottom of inning
    0-0 count

    How to calculate
    re_count[C2] - re_count[B3]
    """
    playEvents_dict = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 0,
            'strikes': 1,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': 2,
                'pZ': 4
            }
        }
    }

    runners = [False, False, False]
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(-.082, abs=1e-3)

def test_calculate_delta_07():
    """
    Ball called Strike
    Top of inning
    2-1 count

    How to calculate
    re_count[D4] - re_count[C5]
    """
    playEvents_dict = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 2,
            'strikes': 2,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': 2,
                'pZ': 4
            }
        }
    }

    runners = [False, False, False]
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(-.181, abs=1e-3)

def test_calculate_delta_08():
    """
    Strike called Ball
    Top of inning
    2-1 count

    How to calculate
    re_count[D4] - re_count[C5]
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 3,
            'strikes': 1,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': .2,
                'pZ': 2.8
            }
        }
    }

    runners = [False, False, False]
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(-.181, abs=1e-3)

def test_calculate_delta_09():
    """
    Strike called Ball
    Top of inning
    2-2 count
    Bases empty

    How to calculate
    re_runners[B3] - (re_runners[B2] + re_count[D5])
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 3,
            'strikes': 2,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': .6,
                'pZ': 2.8
            }
        }
    }

    runners = [False, False, False]
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(-.277, abs=1e-3)

def test_calculate_delta_10():
    """
    Ball called Strike
    Bottom of inning
    1-2 count, 1 out
    Runner on First

    How to calculate
    re_runners[C3] + re_count[D4] - re_runners[C4]
    """
    playEvents_dict = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 1,
            'strikes': 3,
            'outs': 1
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': -3.6,
                'pZ': 4.8
            }
        }
    }

    runners = [True, False, False]
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(-.236, abs=1e-3)

def test_calculate_delta_11():
    """
    Ball called Strike
    Top of inning
    3-2 count, 0 out
    Bases Loaded

    How to calculate
    
    """
    playEvents_dict = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 3,
            'strikes': 3,
            'outs': 0
        },
        'pitchData': {
            'strikeZoneTop': 3.5,
            'strikeZoneBottom': 1.5,
            'coordinates': {
                'pX': -3.6,
                'pZ': 4.8
            }
        }
    }

    runners = [True, True, True]
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.calculate_delta_home_favor(runners, isTopInning)

    assert home_delta == pytest.approx(1.762, abs=1e-3)

