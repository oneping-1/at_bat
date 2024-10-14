# pylint: disable=C0111

import json
import os
from at_bat.game import Game

def open_748534():
    test_file_path = os.path.relpath(__file__)
    j748534 = os.path.join(test_file_path, '..', 'test_json', '748534.json')

    with open(j748534, encoding='utf-8') as f:
        data = json.load(f)

    return data

def test_game_initiation():
    data = open_748534()
    assert data['gamePk'] == 748534

    game = Game(data)
    assert game.gamepk == 748534

    assert game.gameData.teams.away.abbreviation == 'TEX'
    assert game.gameData.teams.home.abbreviation == 'AZ'

    assert game.liveData.linescore.teams.away.runs == 5
    assert game.liveData.linescore.teams.home.runs == 0

    assert game.liveData.decisions.winner.fullName == 'Nathan Eovaldi'
    assert game.liveData.decisions.loser.fullName == 'Zac Gallen'

    assert game.liveData.plays.currentPlay.result.eventType == 'strikeout'
    assert game.liveData.plays.currentPlay.matchup.batter.fullName == 'Ketel Marte'
    assert game.liveData.plays.currentPlay.matchup.pitcher.fullName == 'Josh Sborz'

    assert game.liveData.plays.allPlays[66].atBatIndex == 66
    assert game.liveData.plays.allPlays[66].about.inning == 9
    assert game.liveData.plays.allPlays[66].about.isTopInning is True
    s = 'Josh Jung singles on a sharp line drive to center fielder Alek Thomas.'
    assert game.liveData.plays.allPlays[66].result.description == s

if __name__ == '__main__':
    print(open_748534())
