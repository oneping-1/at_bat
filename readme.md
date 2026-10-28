# MLB Stat

Live MLB and MiLB game stats.

## Table of Contents

- [Installation](#Installation)
- [To-Do](#to-do)

## Installation

In the command prompt, navigate to the directory and type
- pip install -r requirements.txt
- pip install -e .

## To-Do

Incomplete:
- [ ] Move strenght_of_schedule.py calculations into own method in get.teams.py
- [ ] Add miss_distance variable or something to indicate how far a pitch was from the edge of the zone in class PitchCoordinates
- [ ] Redo umpire module to utilize faster pandas dataframe
- [ ] Figure out a good work around for the count logic. Like a strikeout goes 0-2 1 out -> 0-3 1 out -> 0-3 2 out -> 0-0 2 out