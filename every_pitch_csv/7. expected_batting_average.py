import os
import csv
import tqdm
import numpy as np
import pandas as pd
from typing import List, Tuple

EV_BIN_WIDTH = 3
LA_BIN_WIDTH = 1

IGNORE = (
    'field_error',
    'sac_fly',
    'catchers_interf',
    'sac_bunt',
    'sac_fly_double_play', # only 3 in 2024. not sure it should count against batter
)

OUTS = (
    'field_out',
    'force_out',
    'grounded_into_double_play',
    'fielders_choice',
    'fielders_choice_out',
    'double_play',
)

HITS = {
    'single': 1,
    'double': 2,
    'triple': 3,
    'home_run': 4,
}

def read_pitch_csv() -> pd.DataFrame:
    """
    Read the pitch.csv file and return it as a pandas DataFrame.

    Returns:
        pd.DataFrame: A pandas DataFrame with the contents of the
            pitch.csv file.
    """
    # Read the csv file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 'pitch.csv')
    df = pd.read_csv(csv_file_path)
    return df


def create_dict() -> dict:
    # 2024 Min EV:   9.1 mph
    # 2024 Max EV: 121.5 mph
    # 2024 Min LA: -90 deg
    # 2024 Max LA:  90 deg

    ev_range = np.arange(5, 130, .1)
    ev_range = ev_range.tolist()
    ev_range = [round(x,1) for x in ev_range]
    # ev_range = [str(x) for x in ev_range]

    la_range = np.arange(-100, 100, 1)
    la_range = la_range.tolist()
    la_range = [round(x) for x in la_range]
    # la_range = [str(x) for x in la_range]

    combo = {}

    for ev in ev_range:
        for la in la_range:
            combo[(ev, la)] = {
                'h': 0,
                'tb': 0,
                'ab': 0,
            }

    return combo


def find_acceptable_states(state: Tuple[float, float]) -> List[Tuple[float, float]]:
    ev, la = state

    min_ev = ev - EV_BIN_WIDTH
    max_ev = ev + EV_BIN_WIDTH

    min_la = la - LA_BIN_WIDTH
    max_la = la + LA_BIN_WIDTH

    ev_range = np.arange(min_ev, max_ev, .1)
    ev_range = ev_range.tolist()
    ev_range = [round(x,1) for x in ev_range]

    la_range = np.arange(min_la, max_la, 1)
    la_range = la_range.tolist()
    la_range = [round(x) for x in la_range]

    state_range = []

    for ev in ev_range:
        for la in la_range:
            state_range.append((ev, la))

    return state_range


def write_values(lookup_table: dict):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # csv_path = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(current_dir, 'expected_values.csv')

    with open(csv_file_path, 'w', encoding='utf-8') as csv_file:
        field_names = ['exit_velocity', 'launch_angle', 'xba', 'xslg', 'hits', 'total_bases', 'at_bats']
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for key, value in lookup_table.items():
            writer.writerow({
                'exit_velocity': key[0],
                'launch_angle': key[1],
                'xba': value['xba'],
                'xslg': value['xslg'],
                'hits': value['h'],
                'total_bases': value['tb'],
                'at_bats': value['ab']
            })


def main():
    df = read_pitch_csv()
    lookup_table = create_dict()

    for _, row in tqdm.tqdm(df.iterrows()):
        at_bat_result = row['at_bat_event_type']
        exit_velocity = row['batted_ball_launch_speed']
        launch_angle = row['batted_ball_launch_angle']

        if pd.isnull(exit_velocity) or pd.isnull(launch_angle):
            continue

        if at_bat_result in IGNORE:
            continue

        state = (exit_velocity, launch_angle)
        states = find_acceptable_states(state)
        if at_bat_result in OUTS :
            for s in states:
                lookup_table[s]['ab'] += 1
            continue

        if at_bat_result in HITS:
            for s in states:
                lookup_table[s]['ab'] += 1
                lookup_table[s]['h'] += 1
                lookup_table[s]['tb'] += HITS[at_bat_result]
            continue

    for key, value in lookup_table.items():
        if value['ab'] == 0:
            value['xba'] = None
            value['xslg'] = None
            continue
        value['xba'] = value['h'] / value['ab']
        value['xslg'] = value['tb'] / value['ab']
        if 89 <= key[0] <= 91 and 9 <= key[1] <= 11:
            print(key, value)

    write_values(lookup_table)
    return lookup_table

if __name__ == '__main__':
    main()
