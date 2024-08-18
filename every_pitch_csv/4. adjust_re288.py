"""
The previous module "3. compute.py" creates a RE288 run expectancy
matrix. That module holds data for states from balls 0-3,
strikes 0-2, outs 0-2, and runners on base 0-7. This module adds
states for ball 4, strike 3, and out 3 so that an error wont be
thrown when trying to access a state. The MLB api makes it possible
to have a state for ball 4, strike 3 and out 3 while waiting for
the new batter.

This module will create a new run expectancy matrix with the
new states by copying the old matrix and adding the new states.
The new states will be calculated by using the old states.
"""

import csv
import os
import itertools

def eval_base(base: str) -> bool:
    if base == 'False':
        return False
    if base == 'True':
        return True
    raise ValueError(f'Invalid value for base: {base}')

def read_re288() -> dict:
    """Reads the run expectancy csv file

    Key: Tuple[int, int, int, int, int, int]
        (balls, strikes, outs, is_first, is_second, is_third)
    Value: float
        run expectancy"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # csv_path = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(current_dir, 're288.csv')

    run_expectancy = {}

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            balls = int(row[0])
            strikes = int(row[1])
            outs = int(row[2])
            is_first_base = eval_base(row[3])
            is_second_base = eval_base(row[4])
            is_third_base = eval_base(row[5])

            total_runs = float(row[6])
            count = int(row[7])
            runs = float(row[8])
            runs0 = int(row[9])
            runs1 = int(row[10])
            runs2 = int(row[11])
            runs3 = int(row[12])
            runs4 = int(row[13])
            runs5 = int(row[14])
            runs6 = int(row[15])
            runs7 = int(row[16])
            runs8 = int(row[17])
            runs9 = int(row[18])
            runs10 = int(row[19])
            runs11 = int(row[20])
            runs12 = int(row[21])
            runs13 = int(row[22])

            state = (balls, strikes, outs, is_first_base, is_second_base, is_third_base)
            run_expectancy[state] = {'total_runs': total_runs, 'count': count, 'average_runs': runs, '0 runs': runs0, '1 runs': runs1, '2 runs': runs2, '3 runs': runs3, '4 runs': runs4, '5 runs': runs5, '6 runs': runs6, '7 runs': runs7, '8 runs': runs8, '9 runs': runs9, '10 runs': runs10, '11 runs': runs11, '12 runs': runs12, '13 runs': runs13}

    return run_expectancy

def create_re640():
    """
    Creates re640 run expectancy matrix.

    Adjusts the run expectancy matrix to include states for ball 4,
    strike 3, and out 3. The new states will be calculated by using
    the old states.
    """

    re288 = read_re288()

    balls = list(range(5))
    strikes = list(range(4))
    outs = list(range(4))
    is_first_base = [False, True]
    is_second_base = [False, True]
    is_third_base = [False, True]

    states = itertools.product(balls, strikes, outs, is_first_base, is_second_base, is_third_base)
    re640 = {state: None for state in states}

    for key, _ in re640.items():
        balls = key[0]
        strikes = key[1]
        outs = key[2]
        is_first_base = key[3]
        is_second_base = key[4]
        is_third_base = key[5]

        if (balls == 4) and (strikes == 3):
            # not possible
            re640[key] = {'total_runs': None, 'count': None, 'average_runs': None, '0 runs': None, '1 runs': None, '2 runs': None, '3 runs': None, '4 runs': None, '5 runs': None, '6 runs': None, '7 runs': None, '8 runs': None, '9 runs': None, '10 runs': None, '11 runs': None, '12 runs': None, '13 runs': None}
        elif (outs == 3) or ((strikes == 3) and (outs == 2)):
            # end of inning
            re640[key] = {'total_runs': 0, 'count': 0, 'average_runs': 0, '0 runs': 0, '1 runs': 0, '2 runs': 0, '3 runs': 0, '4 runs': 0, '5 runs': 0, '6 runs': 0, '7 runs': 0, '8 runs': 0, '9 runs': 0, '10 runs': 0, '11 runs': 0, '12 runs': 0, '13 runs': 0}
        elif strikes == 3:
            re640[key] = re288[(0, 0, outs + 1, is_first_base, is_second_base, is_third_base)]
        elif balls == 4:
            if (is_first_base == 0) and (is_second_base == 0) and (is_third_base == 0):
                re640[key] = re288[(0, 0, outs, 1, 0, 0)]
            elif (is_first_base == 1) and (is_second_base == 0) and (is_third_base == 0):
                re640[key] = re288[(0, 0, outs, 1, 1, 0)]
            elif (is_first_base == 0) and (is_second_base == 1) and (is_third_base == 0):
                re640[key] = re288[(0, 0, outs, 1, 1, 0)]
            elif (is_first_base == 1) and (is_second_base == 1) and (is_third_base == 0):
                re640[key] = re288[(0, 0, outs, 1, 1, 1)]
            elif (is_first_base == 0) and (is_second_base == 0) and (is_third_base == 1):
                re640[key] = re288[(0, 0, outs, 1, 0, 1)]
            elif (is_first_base == 1) and (is_second_base == 0) and (is_third_base == 1):
                re640[key] = re288[(0, 0, outs, 1, 1, 1)]
            elif (is_first_base == 0) and (is_second_base == 1) and (is_third_base == 1):
                re640[key] = re288[(0, 0, outs, 1, 1, 1)]
            elif (is_first_base == 1) and (is_second_base == 1) and (is_third_base == 1):
                re640[key] = re288[(0, 0, outs, 1, 1, 1)]
        elif (balls < 4) and (strikes < 3) and (outs < 3):
            re640[key] = re288[key]

    return(re640)

def write_re640(run_expectancy: dict):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # csv_path = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(current_dir, 're640.csv')

    with open(csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        field_names = ['balls', 'strikes', 'outs', 'is_first_base', 'is_second_base', 'is_third_base', 'total_runs', 'count', 'average_runs', '0 runs', '1 runs', '2 runs', '3 runs', '4 runs', '5 runs', '6 runs', '7 runs', '8 runs', '9 runs', '10 runs', '11 runs', '12 runs', '13 runs']
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for key, value in run_expectancy.items():
            writer.writerow({
                'balls': key[0],
                'strikes': key[1],
                'outs': key[2],
                'is_first_base': key[3],
                'is_second_base': key[4],
                'is_third_base': key[5],
                'total_runs': value['total_runs'],
                'count': value['count'],
                'average_runs': value['average_runs'],
                '0 runs': value['0 runs'],
                '1 runs': value['1 runs'],
                '2 runs': value['2 runs'],
                '3 runs': value['3 runs'],
                '4 runs': value['4 runs'],
                '5 runs': value['5 runs'],
                '6 runs': value['6 runs'],
                '7 runs': value['7 runs'],
                '8 runs': value['8 runs'],
                '9 runs': value['9 runs'],
                '10 runs': value['10 runs'],
                '11 runs': value['11 runs'],
                '12 runs': value['12 runs'],
                '13 runs': value['13 runs']
            })

def create_red288(re640: dict) -> dict:
    re288 = read_re288()

    red288 = {}

    for key, _ in re288.items():
        balls = key[0]
        strikes = key[1]
        outs = key[2]
        is_first_base = key[3]
        is_second_base = key[4]
        is_third_base = key[5]

        ball_state = (balls + 1, strikes, outs, is_first_base, is_second_base, is_third_base)
        strike_state = (balls, strikes + 1, outs, is_first_base, is_second_base, is_third_base)

        ball_runs = re640[ball_state]['average_runs']
        strike_runs = re640[strike_state]['average_runs']

        if (balls == 3) and (is_first_base is True) and (is_second_base is True) and (is_third_base is True):
            # walk in a run
            # not accounted for in re640 because that only looks at
            # runs scored from that point onward and ignores walked in run
            ball_runs += 1

        red288[key] = ball_runs - strike_runs
        print(f'{key}: {red288[key]}')

    return red288

def write_red288(red288: dict):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # csv_path = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(current_dir, 'red288.csv')

    with open(csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        field_names = ['balls', 'strikes', 'outs', 'is_first_base', 'is_second_base', 'is_third_base', 'run_value']
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for key, value in red288.items():
            writer.writerow({
                'balls': key[0],
                'strikes': key[1],
                'outs': key[2],
                'is_first_base': key[3],
                'is_second_base': key[4],
                'is_third_base': key[5],
                'run_value': value
            })

def main():
    re640 = create_re640()
    write_re640(re640)
    write_red288(create_red288(re640))
    print('done')

if __name__ == '__main__':
    main()
