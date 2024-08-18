import csv
import os
import itertools
from tqdm import tqdm

def eval_base(base: str) -> bool:
    if base == 'False':
        return False
    if base == 'True':
        return True
    raise ValueError(f'Invalid value for base: {base}')


def read_wp316224() -> dict:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 'wp316224.csv')

    wp316224 = {}

    with open(csv_file_path, 'r', newline='', encoding='UTF-8') as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            key = (
                int(row['balls']),
                int(row['strikes']),
                int(row['outs']),
                eval_base(row['is_first_base']),
                eval_base(row['is_second_base']),
                eval_base(row['is_third_base']),
                int(row['inning']),
                eval_base(row['is_top_inning']),
                int(row['home_lead'])
            )

            wp316224[key] = {
                'away_win': float(row['away_win']),
                'home_win': float(row['home_win']),
                'tie': float(row['tie'])
            }

    return wp316224

def create_wp702720(wp316224: dict) -> dict:

    # Possible states
    balls = list(range(5))
    strikes = list(range(4))
    outs = list(range(4))
    is_first_base = [False, True]
    is_second_base = [False, True]
    is_third_base = [False, True]
    inning = list(range(1, 10))
    is_top_inning = [False, True]
    home_lead = list(range(-30, 31))

    states = itertools.product(balls, strikes, outs, is_first_base, is_second_base, is_third_base, inning, is_top_inning, home_lead)
    wp702720 = {state: None for state in states}

    for key, _ in tqdm(wp702720.items()):
        balls = key[0]
        strikes = key[1]
        outs = key[2]
        is_first_base = key[3]
        is_second_base = key[4]
        is_third_base = key[5]
        inning = key[6]
        is_top_inning = key[7]
        home_lead = key[8]

        if (balls == 4) and (strikes == 3):
            # not possible
            wp702720[key] = {'away_win': None, 'home_win': None, 'tie': None}
        elif (outs == 3) or ((strikes == 3) and (outs == 2)):
            # end of half inning
            if key[7] is True:
                # middle of inning
                equal_state = (0, 0, 0, False, False, False, inning, False, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif key[7] is False:
                # end of inning
                # extra innings. revert to 9th
                if inning == 9:
                    equal_state = (0, 0, 0, False, False, False, 9, True, home_lead)
                else:
                    equal_state = (0, 0, 0, False, False, False, inning + 1, True, home_lead)
                wp702720[key] = wp316224[equal_state]
        elif strikes == 3:
            # strike 3
            equal_state = (0, 0, outs + 1, is_first_base, is_second_base, is_third_base, inning, is_top_inning, home_lead)
            wp702720[key] = wp316224[equal_state]
        elif balls == 4:
            if is_top_inning is True:
                d = -1
            elif is_top_inning is False:
                d = 1

            if (is_first_base == 0) and (is_second_base == 0) and (is_third_base == 0):
                equal_state = (0, 0, outs, 1, 0, 0, inning, is_top_inning, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif (is_first_base == 1) and (is_second_base == 0) and (is_third_base == 0):
                equal_state = (0, 0, outs, 1, 1, 0, inning, is_top_inning, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif (is_first_base == 0) and (is_second_base == 1) and (is_third_base == 0):
                equal_state = (0, 0, outs, 1, 1, 0, inning, is_top_inning, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif (is_first_base == 1) and (is_second_base == 1) and (is_third_base == 0):
                equal_state = (0, 0, outs, 1, 1, 1, inning, is_top_inning, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif (is_first_base == 0) and (is_second_base == 0) and (is_third_base == 1):
                equal_state = (0, 0, outs, 1, 0, 1, inning, is_top_inning, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif (is_first_base == 1) and (is_second_base == 0) and (is_third_base == 1):
                equal_state = (0, 0, outs, 1, 1, 1, inning, is_top_inning, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif (is_first_base == 0) and (is_second_base == 1) and (is_third_base == 1):
                equal_state = (0, 0, outs, 1, 1, 1, inning, is_top_inning, home_lead)
                wp702720[key] = wp316224[equal_state]
            elif (is_first_base == 1) and (is_second_base == 1) and (is_third_base == 1):
                if abs(home_lead) == 30:
                    # most runs scored in recent history is 30
                    # so that is the max lead
                    # a walk with bases loaded will not increase the lead
                    # but doesnt really matter because 30 run lead is a win
                    equal_state = (0, 0, outs, 1, 1, 1, inning, is_top_inning, home_lead)
                    wp702720[key] = wp316224[equal_state]
                else:
                    equal_state = (0, 0, outs, 1, 1, 1, inning, is_top_inning, home_lead + d)
                    wp702720[key] = wp316224[equal_state]
        else:
            # all other states
            equal_state = (balls, strikes, outs, is_first_base, is_second_base, is_third_base, inning, is_top_inning, home_lead)
            wp702720[key] = wp316224[equal_state]

    return wp702720

def write_wp702720(wp702720: dict):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 'wp702720.csv')

    with open(csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        fieldnames = [
            'balls',
            'strikes',
            'outs',
            'is_first_base',
            'is_second_base',
            'is_third_base',
            'inning',
            'is_top_inning',
            'home_lead',
            'away_win',
            'home_win',
            'tie'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for key, value in tqdm(wp702720.items()):
            writer.writerow({
                'balls': key[0],
                'strikes': key[1],
                'outs': key[2],
                'is_first_base': key[3],
                'is_second_base': key[4],
                'is_third_base': key[5],
                'inning': key[6],
                'is_top_inning': key[7],
                'home_lead': key[8],
                'away_win': value['away_win'],
                'home_win': value['home_win'],
                'tie': value['tie']
            })

def main():
    wp316224 = read_wp316224()
    wp702720 = create_wp702720(wp316224)
    write_wp702720(wp702720)

if __name__ == '__main__':
    main()
