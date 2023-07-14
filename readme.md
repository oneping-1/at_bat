# MLB Stat

Live MLB (and potentially minor league) game stats.
Umpire.py is an attempt to recreate Ump Scorecards (https://twitter.com/UmpScorecards). Has multiple functions that essentially do the same thing

## Table of Contents

- [To-Do](#to-do)

## To-Do

- [X] Add delta_seconds parameter to umpire.print_last_pitch() function
- [X] Implement 4-D Run Expectency table
- [X] Make optional function parameter to print every missed pitch in umpire.umpire()
- [ ] Add runners variable directly to get.game.LiveData class
- [X] Add readme
- [X] Implement Ump Scorecards method to calculate if pitch was in the zone
- [ ] Implement Margin of Error method to calculate if pitch was in the zone
- [X] Update and add more pytests
- [ ] Add restructured text doc strings for functions, classes
- [X] Shows expected runs in the inning in umpire.show_last_pitch()
- [ ] Fix Bug with umpire.print_every_pitch()