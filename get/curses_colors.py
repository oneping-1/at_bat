# pylint: disable=W0702

import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, min(255, curses.COLORS)):
        curses.init_pair(i + 1, i, -1)
    try:
        for i in range(0, 255):
            stdscr.addstr(f'{i:03d} ', curses.color_pair(i))
    except:
        # End of screen reached
        pass
    stdscr.getch()

if __name__ == '__main__':
    curses.wrapper(main)
