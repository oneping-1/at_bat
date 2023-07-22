# pylint: disable=C0103

import pytest
from get.game import PlayEvents, Runners

# https://community.fangraphs.com/the-effect-of-umpires-on-baseball-umpire-runs-created-urc/

def test_calculate_delta_00():
    """
    Ball called Strike
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
                'pX': -1,
                'pZ': 2
            },
            'zone': 5
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    assert home_delta_monte == pytest.approx(.1, abs=1e-3)

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
            },
            'zone': 5
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.delta_favor_zone(int(runners), isTopInning)

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
            },
            'zone': 11
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta = pitch.delta_favor_zone(int(runners), isTopInning)

    assert home_delta == 0

def test_calculate_delta_03():
    """
    Ball called Strike
    Bottom of inning
    1-0 count

    2023-06-20 NYM at HOU
    Bottom 2, Verlander to Diaz
    https://twitter.com/UmpScorecards/status/1671526204338257923
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=called%5C.%5C.strike%7C&hfZ=11%7C12%7C13%7C14%7C&hfStadium=2392%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-06-20&game_date_lt=2023-06-20&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
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

    runners = Runners(runners_list=[False, False, False])
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Ump Scorecards has -0.11
    # Fangraphs RE = -0.12
    # Fangraphs RED = -0.13
    assert home_delta_zone == pytest.approx(-.13, abs=1e-3)
    assert home_delta_monte == pytest.approx(-.13, abs=1e-3)

def test_calculate_delta_04():
    """
    Strike called ball
    Bottom of inning
    3-1 count

    2023-06-20 NYM at HOU
    Top 7, Valdez to Lindor
    https://twitter.com/UmpScorecards/status/1671526204338257923
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=2392%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-06-20&game_date_lt=2023-06-20&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
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

    runners = Runners(runners_list=[False, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Did not show on Ump Scorecards
    assert home_delta_zone == pytest.approx(-.1, abs=1e-3)
    assert home_delta_monte == 0

def test_calculate_delta_05():
    """
    Strike called Ball
    Top of inning
    0-1 count

    2023-06-13 TB at OAK
    Top 4, Harris to Paredes
    https://twitter.com/UmpScorecards/status/1669006670897266690
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=10%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-06-13&game_date_lt=2023-06-13&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 1,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.27,
            'strikeZoneBottom': 1.50,
            'coordinates': {
                'pX': -0.79,
                'pZ': 2.06
            },
            'zone': 4
        }
    }

    runners = Runners(runners_list=[True, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Ump Scorecards has -0.08
    assert home_delta_zone == pytest.approx(-0.08, abs=1e-3)
    assert home_delta_monte == pytest.approx(-0.08, abs=1e-3)

def test_calculate_delta_06():
    """
    Strike called Ball
    Bottom of inning
    2-1 count

    2023-05-28 TEX at BAL
    Bottom 8, Ragans to Rutschman
    https://twitter.com/UmpScorecards/status/1663191326714634240
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=called%5C.%5C.strike%7C&hfZ=11%7C12%7C13%7C14%7C&hfStadium=2%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C2022%7C2021%7C2020%7C2019%7C2018%7C2017%7C2016%7C2015%7C2014%7C2013%7C2012%7C2011%7C2010%7C2009%7C2008%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-28&game_date_lt=2023-05-28&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=8%7C&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
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
            'strikeZoneTop': 3.37370384468164,
            'strikeZoneBottom': 1.62742076652336,
            'coordinates': {
                'pX': 0.2710530314580832,
                'pZ': 3.518891508624232
            },
            'zone': 12
        }
    }

    runners = Runners(runners_list=[True, False, False])
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Did not show on Ump Scorecards
    assert home_delta_zone == pytest.approx(-0.28, abs=1e-3)
    assert home_delta_monte == 0

def test_calculate_delta_07():
    """
    Strike called Ball
    Top of inning
    0-0 count

    2023-05-28 TEX at BAL
    Top 7, Bradish to Jung
    https://twitter.com/UmpScorecards/status/1663191326714634240
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=2%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C2022%7C2021%7C2020%7C2019%7C2018%7C2017%7C2016%7C2015%7C2014%7C2013%7C2012%7C2011%7C2010%7C2009%7C2008%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-28&game_date_lt=2023-05-28&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 0,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.65,
            'strikeZoneBottom': 1.71,
            'coordinates': {
                'pX': 0.82,
                'pZ': 3.27
            },
            'zone': 3
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Did not show on Ump Scorecards
    assert home_delta_zone == pytest.approx(-0.03, abs=1e-3)
    assert home_delta_monte == 0

def test_calculate_delta_08():
    """
    Strike called Ball
    Top of inning
    0-0 count

    2023-05-28 TEX at BAL
    Top 8, Cano to Taveras
    https://twitter.com/UmpScorecards/status/1663191326714634240
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=2%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C2022%7C2021%7C2020%7C2019%7C2018%7C2017%7C2016%7C2015%7C2014%7C2013%7C2012%7C2011%7C2010%7C2009%7C2008%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-28&game_date_lt=2023-05-28&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
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
            'strikeZoneTop': 3.67,
            'strikeZoneBottom': 1.76,
            'coordinates': {
                'pX': 0.69,
                'pZ': 2.06
            },
            'zone': 9
        }
    }

    runners = Runners(runners_list=[True, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Ump Scorecards had -0.14
    assert home_delta_zone == pytest.approx(-0.15, abs=1e-3)
    assert home_delta_monte == pytest.approx(-0.15, abs=1e-3)

def test_calculate_delta_09():
    """
    Strike called Ball
    Top of inning
    0-0 count

    2023-05-28 TEX at BAL
    Top 7, Bradish to Jung
    https://twitter.com/UmpScorecards/status/1663191326714634240
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=2%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C2022%7C2021%7C2020%7C2019%7C2018%7C2017%7C2016%7C2015%7C2014%7C2013%7C2012%7C2011%7C2010%7C2009%7C2008%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-28&game_date_lt=2023-05-28&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 0,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.65,
            'strikeZoneBottom': 1.71,
            'coordinates': {
                'pX': 0.82,
                'pZ': 3.27
            },
            'zone': 3
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Did not show on Ump Scorecards
    assert home_delta_zone == pytest.approx(-0.03, abs=1e-3)
    assert home_delta_monte == 0

def test_calculate_delta_10():
    """
    Strike called Ball
    Bottom of inning
    0-2 count

    2023-05-16 TB at NYM
    Bottom 3, Chirinos to Nimmo
    https://twitter.com/UmpScorecards/status/1658843190533795849
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=3289%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-16&game_date_lt=2023-05-16&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 2,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.35,
            'strikeZoneBottom': 1.69,
            'coordinates': {
                'pX': -0.78,
                'pZ': 2.8
            },
            'zone': 4
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Ump Scorecards had +0.07
    assert home_delta_zone == pytest.approx(+0.07, abs=1e-3)
    assert home_delta_monte == pytest.approx(+0.07, abs=1e-3)

def test_calculate_delta_11():
    """
    Strike called Ball
    Bottom of inning
    0-0 count

    2023-05-16 TB at NYM
    Bottom 1, Chirinos to Nimmo
    https://twitter.com/UmpScorecards/status/1658843190533795849
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=3289%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-16&game_date_lt=2023-05-16&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 1,
            'strikes': 0,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.33,
            'strikeZoneBottom': 1.69,
            'coordinates': {
                'pX': 0.82,
                'pZ': 3.34
            },
            'zone': 4
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Did not show on Ump Scorecards
    assert home_delta_zone == pytest.approx(+0.03, abs=1e-3)
    assert home_delta_monte == 0

def test_calculate_delta_12():
    """
    Ball called Strike
    Bottom Inning
    0-0 Count

    2023-05-09 KC at CWS
    Bottom 1, Giolito to Perez
    https://twitter.com/UmpScorecards/status/1656307096244178944?ref_src=twsrc%5Etfw%7Ctwcamp%5Etweetembed%7Ctwterm%5E1656307096244178944%7Ctwgr%5Eb4708cf6080193477a5b007d6809baf6a33b64ca%7Ctwcon%5Es1_&ref_url=https%3A%2F%2Fumpscorecards.com%2Fsingle_game%2F%3Fgame_id%3D718238
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=called%5C.%5C.strike%7C&hfZ=11%7C12%7C13%7C14%7C&hfStadium=7%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-09&game_date_lt=2023-05-09&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'C'
        },
        'count': {
            'balls': 0,
            'strikes': 1,
            'outs': 1
        },
        'pitchData': {
            'strikeZoneTop': 3.69,
            'strikeZoneBottom': 1.69,
            'coordinates': {
                'pX': 1.03,
                'pZ': 2.27
            },
            'zone': 14
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = False

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Ump Scorecards had -0.05
    assert home_delta_zone == pytest.approx(-0.06, abs=1e-3)
    assert home_delta_monte == pytest.approx(-0.06, abs=1e-3)

def test_calculate_delta_13():
    """
    Strike called ball
    Bottom Inning
    1-2 Count

    2023-05-09 KC at CWS
    Top 2, Giolito to Perez
    https://twitter.com/UmpScorecards/status/1656307096244178944?ref_src=twsrc%5Etfw%7Ctwcamp%5Etweetembed%7Ctwterm%5E1656307096244178944%7Ctwgr%5Eb4708cf6080193477a5b007d6809baf6a33b64ca%7Ctwcon%5Es1_&ref_url=https%3A%2F%2Fumpscorecards.com%2Fsingle_game%2F%3Fgame_id%3D718238
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=7%7C&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-05-09&game_date_lt=2023-05-09&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 2,
            'strikes': 2,
            'outs': 1
        },
        'pitchData': {
            'strikeZoneTop': 3.08087458992998,
            'strikeZoneBottom': 1.45858003668385,
            'coordinates': {
                'pX': -0.8026750052835597,
                'pZ': 1.4342317987795377
            },
            'zone': 7
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Did not show on ump scorecards
    assert home_delta_zone == pytest.approx(-0.15, abs=1e-3)
    assert home_delta_monte == 0

def test_calculate_delta_14():
    """
    Strike called ball
    Top Inning
    1-2 Count

    2023-06-11 NL at AL
    Top 6, Cano to Riley
    https://twitter.com/UmpScorecards/status/1679143754010075138/photo/1
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=A%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-07-11&game_date_lt=2023-07-11&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&batters_lookup%5B%5D=663586&hfFlag=&pitchers_lookup%5B%5D=666974&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 2,
            'strikes': 2,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.52,
            'strikeZoneBottom': 1.58,
            'coordinates': {
                'pX': 0.77,
                'pZ': 2.81
            },
            'zone': 6
        }
    }

    runners = Runners(runners_list=[True, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Was on Ump Scorecards
    assert home_delta_zone == pytest.approx(-0.19, abs=1e-3)
    assert home_delta_monte == pytest.approx(-0.19, abs=1e-3)

def test_calculate_delta_15():
    """
    Strike called ball
    Top Inning
    2-2 Count

    2023-06-11 NL at AL
    Top 6, Cano to Riley
    https://twitter.com/UmpScorecards/status/1679143754010075138/photo/1
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=A%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-07-11&game_date_lt=2023-07-11&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&batters_lookup%5B%5D=663586&hfFlag=&pitchers_lookup%5B%5D=666974&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 3,
            'strikes': 2,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.52,
            'strikeZoneBottom': 1.55,
            'coordinates': {
                'pX': 0.83,
                'pZ': 2.70
            },
            'zone': 6
        }
    }

    runners = Runners(runners_list=[True, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Was on not Ump Scorecards
    assert home_delta_zone == pytest.approx(-0.26, abs=1e-3)
    assert home_delta_monte == 0

def test_calculate_delta_16():
    """
    Strike called ball
    Top Inning
    3-2 Count

    2023-06-11 NL at AL
    Top 3, Gray to Freeman
    https://twitter.com/UmpScorecards/status/1679143754010075138/photo/1
    https://baseballsavant.mlb.com/statcast_search?hfPTM=&hfPT=&hfAB=&hfGT=A%7C&hfPR=ball%7C&hfZ=1%7C2%7C3%7C4%7C5%7C6%7C7%7C8%7C9%7C&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2023%7C&hfSit=&player_type=pitcher&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2023-07-11&game_date_lt=2023-07-11&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&batters_lookup%5B%5D=518692&hfFlag=&pitchers_lookup%5B%5D=543243&metric_1=&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc#results
    """
    playEvents_dict = {
        'details': {
            'code': 'B'
        },
        'count': {
            'balls': 4,
            'strikes': 2,
            'outs': 2
        },
        'pitchData': {
            'strikeZoneTop': 3.62, # pZ_top = 3.74
            'strikeZoneBottom': 1.86,
            'coordinates': {
                'pX': 0.20,
                'pZ': 3.71
            },
            'zone': 2
        }
    }

    runners = Runners(runners_list=[False, False, False])
    isTopInning = True

    pitch = PlayEvents(playEvents_dict)
    home_delta_zone = pitch.delta_favor_zone(int(runners), isTopInning)
    home_delta_monte = pitch.delta_favor_monte(int(runners), isTopInning)

    # Was on Ump Scorecards
    assert home_delta_zone == pytest.approx(-0.22, abs=1e-3)
    assert home_delta_monte == pytest.approx(-0.22, abs=1e-3)
