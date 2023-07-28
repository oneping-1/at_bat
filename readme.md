# MLB Stat

Live MLB and MiLB game stats.

## Table of Contents

- [To-Do](#to-do)

## To-Do

Incomplete:
- [ ] Add restructured text doc strings for functions, classes (In Progress)
- [ ] Pylint code (In Progress)
- [ ] Make scoreboard.py use curses library
- [ ] More pytests
- [ ] Example Code
- [ ] Move strenght_of_schedule.py calculations into own method in get.teams.py
- [ ] Make scoreboard.py return something. Maybe move to another module?
- [ ] Integrate plotter with rest of code
- [ ] Check if runners variable in live_stats.py has issues with walks
- [ ] Setters and Getters in runners class
- [ ] Fine tune delta_favor_dist()

Complete:
- [X] Add delta_seconds parameter to umpire.print_last_pitch() function
- [X] Implement 4-D Run Expectency table
- [X] Make optional function parameter to print every missed pitch in umpire.umpire()
- [X] Add readme
- [X] Implement Ump Scorecards method to calculate if pitch was in the zone
- [X] Update and add more pytests
- [X] Shows expected runs in the inning in umpire.show_last_pitch()
- [X] Fix in_zone_str() function or something in pitch_last_pitch.py (mainly moe part)
- [X] Add something in print_last_pitch so that it prints something in pitch details for mound visits, timeouts, pickoffs, ect
- [X] Add delay argument to umpire_scorecards.umpire() function
- [X] Fix runners not updating in print_last_pitch()
- [X] Add system arguments to print_last_pitch/umpire
- [X] Add function to return list of runners print_last_pitch lines 52-65 to reduce clutter. Maybe remove part to check if new half inning?
- [X] Create function to turn runners list into readable string. Maybe use a class instead of list? __str__?
- [X] add delay_seconds argument to scoreboard files
- [X] Give scoreboard.py a delay system argument
- [X] get_delta_monte() not returning right sign?
- [X] Refactor, move get_total_favored_runs() into class. Add instance variable of list of missed calls. Maybe another class. Easier to print (not entirely tested)
- [X] Make strength_of_schedule.py return class and then have seperate function print (not entirely tested)
- [X] Create some kind of graphic to show pitch location
- [X] Make plotter adjust pitches to normalized top and bottom of zone
- [X] Make a new function in plotter.py that just outputs pitch location so that it can be unit tested
- [X] Fix runners not updating correctly in umpire calculations. Add seperate class
- [X] Figure out how to match Ump Scorecards
- [X] Implement Margin of Error method to calculate if pitch was in the zone
- [X] Make csv files accessible even when running files from subfolders
- [X] Fix circular import issue between runners.py and game.py
- [X] Write doc strings for get_delta_zone() and get_delta_monte()
- [X] Make delta_favor functions take either runners_int or runners arguments