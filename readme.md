# MLB Stat

Live MLB (and potentially minor league) game stats.
Umpire.py is an attempt to recreate Ump Scorecards (https://twitter.com/UmpScorecards). Has multiple functions that essentially do the same thing

## Table of Contents

- [To-Do](#to-do)

## To-Do

- [X] Add delta_seconds parameter to umpire.print_last_pitch() function
- [X] Implement 4-D Run Expectency table
- [X] Make optional function parameter to print every missed pitch in umpire.umpire()
- [X] Add readme
- [X] Implement Ump Scorecards method to calculate if pitch was in the zone
- [ ] Figure out how to match Ump Scorecards
- [ ] Implement Margin of Error method to calculate if pitch was in the zone
- [X] Update and add more pytests
- [ ] Add restructured text doc strings for functions, classes
- [X] Shows expected runs in the inning in umpire.show_last_pitch()
- [ ] Create some kind of graphic to show pitch location
- [ ] Pylint code
- [ ] Make strength_of_schedule.py return dict or class and then have seperate function print
- [ ] Fix in_zone_str() function or something in pitch_last_pitch.py (mainly moe part)
- [ ] Add something in print_last_pitch so that it prints something in pitch details for mound visits, timeouts, pickoffs, ect
- [ ] Add delay argument to umpire_scorecards.umpire() function
- [ ] Fix runners not updating in print_last_pitch()
- [ ] Add system arguments to print_last_pitch?
- [ ] Add function to return list of runners print_last_pitch lines 52-65 to reduce clutter. Maybe remove part to check if new half inning?
- [ ] Create function to turn runners list into readable string. Maybe use a class instead of list? __str__?
- [ ] add delay_seconds argument to scoreboard files