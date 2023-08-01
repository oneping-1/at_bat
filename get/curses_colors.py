"""
Prints all available curses colors to console. Different consoles
may have different colors so this module can be used to see which
number matches to each color
"""

# pylint: disable=W0702

import curses

def main(stdscr):
    """Prints color and number for each available color"""
    curses.start_color()
    curses.use_default_colors()
    stdscr.clear()
    for i in range(0, 255):
        curses.init_pair(i + 1, i, -1)
    try:
        for i in range(0, 255):
            stdscr.addstr(f'{i:03d} ', curses.color_pair(i+1))
    except:
        # End of screen reached
        pass
    stdscr.getch()

if __name__ == '__main__':
    curses.wrapper(main)
