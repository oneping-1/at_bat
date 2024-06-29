from typing import List
import os
import csv
import itertools
import pandas as pd
import tqdm
from tabulate import tabulate

def read_pitch_csv() -> pd.DataFrame:
    # Read the csv file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 'pitch.csv')
    df = pd.read_csv(csv_file_path)
    return df

def save_run_expectancy_results(results: List[dict]):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    run_expectancy_csv_file_path = os.path.join(current_dir, 're288.csv')

    with open(run_expectancy_csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        field_names = ['balls', 'strikes', 'outs', 'is_first_base', 'is_second_base', 'is_third_base', 'total_runs', 'count', 'average_runs', '0 runs', '1 runs', '2 runs', '3 runs', '4 runs', '5 runs', '6 runs', '7 runs', '8 runs', '9 runs', '10 runs', '11 runs', '12 runs', '13 runs']
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for key, value in results.items():
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
                '0 runs': value['run_probability'][0],
                '1 runs': value['run_probability'][1],
                '2 runs': value['run_probability'][2],
                '3 runs': value['run_probability'][3],
                '4 runs': value['run_probability'][4],
                '5 runs': value['run_probability'][5],
                '6 runs': value['run_probability'][6],
                '7 runs': value['run_probability'][7],
                '8 runs': value['run_probability'][8],
                '9 runs': value['run_probability'][9],
                '10 runs': value['run_probability'][10],
                '11 runs': value['run_probability'][11],
                '12 runs': value['run_probability'][12],
                '13 runs': value['run_probability'][13]
            })

def main():
    df = read_pitch_csv()

    # create win probability matrix
    ball_states = list(range(4))
    strike_states = list(range(3))
    out_states = list(range(3))
    is_first_base = [False, True]
    is_second_base = [False, True]
    is_third_base = [False, True]

    run_expectancy_states = itertools.product(ball_states, strike_states, out_states, is_first_base, is_second_base, is_third_base)

    run_probability = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0}
    run_expectancy = {states: {'total_runs': 0, 'count': 0, 'average_runs': None, 'run_probability': run_probability.copy()} for states in run_expectancy_states}

    for _, row in tqdm.tqdm(df.iterrows()):
        balls = row['balls']
        strikes = row['strikes']
        outs = row['outs']
        is_first_base = row['is_first_base']
        is_second_base = row['is_second_base']
        is_third_base = row['is_third_base']

        if (balls < 4) and (strikes < 3):
            run_expectancy_state = (balls, strikes, outs, is_first_base, is_second_base, is_third_base)

            # run expectancy
            run_expectancy[run_expectancy_state]['total_runs'] += row['runs_to_end']
            run_expectancy[run_expectancy_state]['count'] += 1
            run_expectancy[run_expectancy_state]['average_runs'] = run_expectancy[run_expectancy_state]['total_runs'] / run_expectancy[run_expectancy_state]['count']
            run_expectancy[run_expectancy_state]['run_probability'][row['runs_to_end']] += 1

    run_expectancy_results = []
    for key, value in run_expectancy.items():
        balls = key[0]
        strikes = key[1]
        outs = key[2]
        is_first_base = bool(key[3])
        is_second_base = bool(key[4])
        is_third_base = bool(key[5])

        avg_runs = value['average_runs']

        run_expectancy_results.append([balls, strikes, outs, is_first_base, is_second_base, is_third_base, avg_runs])

    save_run_expectancy_results(run_expectancy)
    print(tabulate(run_expectancy_results, headers=['balls', 'strikes', 'outs', 'is_first_base', 'is_second_base', 'is_third_base', 'avg_runs', '1+ runs', '2+ runs', '3+ runs', '4+ runs'], floatfmt='.4f', tablefmt='rounded_outline'))

if __name__ == '__main__':
    main()
