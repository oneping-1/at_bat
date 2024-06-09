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
        field_names = ['balls', 'strikes', 'outs', 'is_first_base', 'is_second_base', 'is_third_base', 'total_runs', 'count', 'average_runs', '1+ runs', '2+ runs', '3+ runs', '4+ runs']
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
                '1+ runs': value['1+ runs'],
                '2+ runs': value['2+ runs'],
                '3+ runs': value['3+ runs'],
                '4+ runs': value['4+ runs']
            })

def save_win_probability_results(results: List[dict]):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    win_probability_csv_file_path = os.path.join(current_dir, 'wp491905.csv')

    with open(win_probability_csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        field_names = ['balls', 'strikes', 'outs', 'is_first_base', 'is_second_base', 'is_third_base', 'inning', 'is_top_inning', 'home_lead', 'total_wins', 'count', 'average_wins']
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
                'inning': key[6],
                'is_top_inning': key[7],
                'home_lead': key[8],
                'total_wins': value['total_wins'],
                'count': value['count'],
                'average_wins': value['average_wins']
            })

def main():
    df = read_pitch_csv()

    # create win probability matrix
    ball_states = list(range(4))
    strike_states = list(range(3))
    out_states = list(range(3))
    is_first = [False, True]
    is_second = [False, True]
    is_third = [False, True]
    inning = list(range(1,15)) # longest game in 2023 was 14 innings
    is_top_inning = [True, False]
    home_lead = list(range(-30, 31))

    run_expectancy_states = itertools.product(ball_states, strike_states, out_states, is_first, is_second, is_third)
    win_probability_state = itertools.product(ball_states, strike_states, out_states, is_first, is_second, is_third, inning, is_top_inning, home_lead)

    run_expectancy = {states: {'total_runs': 0, 'count': 0, 'average_runs': None, '1+ runs': 0, '2+ runs': 0, '3+ runs': 0, '4+ runs': 0} for states in run_expectancy_states}
    win_probability = {states: {'total_wins': 0, 'count': 0, 'average_wins': None} for states in win_probability_state}

    for _, row in tqdm.tqdm(df.iterrows()):
        balls = row['balls']
        strikes = row['strikes']
        outs = row['outs']
        is_first = row['is_first_base']
        is_second = row['is_second_base']
        is_third = row['is_third_base']
        inning = row['inning']
        is_top_inning = row['is_top_inning']
        home_lead = row['home_score'] - row['away_score']

        if (balls < 4) and (strikes < 3):
            run_expectancy_state = (balls, strikes, outs, is_first, is_second, is_third)
            win_probability_state = (balls, strikes, outs, is_first, is_second, is_third, inning, is_top_inning, home_lead)

            # run expectancy
            run_expectancy[run_expectancy_state]['total_runs'] += row['runs_to_end']
            run_expectancy[run_expectancy_state]['count'] += 1
            run_expectancy[run_expectancy_state]['average_runs'] = run_expectancy[run_expectancy_state]['total_runs'] / run_expectancy[run_expectancy_state]['count']

            if row['runs_to_end'] >= 1:
                run_expectancy[run_expectancy_state]['1+ runs'] += 1
            if row['runs_to_end'] >= 2:
                run_expectancy[run_expectancy_state]['2+ runs'] += 1
            if row['runs_to_end'] >= 3:
                run_expectancy[run_expectancy_state]['3+ runs'] += 1
            if row['runs_to_end'] >= 4:
                run_expectancy[run_expectancy_state]['4+ runs'] += 1

            # win probability
            if row['home_final_score'] > row['away_final_score']:
                win_probability[win_probability_state]['total_wins'] += 1
            else:
                # not needed, but for clarity
                win_probability[win_probability_state]['total_wins'] += 0

            win_probability[win_probability_state]['count'] += 1
            win_probability[win_probability_state]['average_wins'] = win_probability[win_probability_state]['total_wins'] / win_probability[win_probability_state]['count']

    run_expectancy_results = []
    for key, value in run_expectancy.items():
        balls = key[0]
        strikes = key[1]
        outs = key[2]
        is_first = bool(key[3])
        is_second = bool(key[4])
        is_third = bool(key[5])

        avg_runs = value['average_runs']
        runs1 = value['1+ runs']
        runs2 = value['2+ runs']
        runs3 = value['3+ runs']
        runs4 = value['4+ runs']

        run_expectancy_results.append([balls, strikes, outs, is_first, is_second, is_third, avg_runs, runs1, runs2, runs3, runs4])

    save_run_expectancy_results(run_expectancy)
    save_win_probability_results(win_probability)
    print(tabulate(run_expectancy_results, headers=['balls', 'strikes', 'outs', 'is_first', 'is_second', 'is_third', 'avg_runs', '1+ runs', '2+ runs', '3+ runs', '4+ runs'], floatfmt='.4f', tablefmt='rounded_outline'))

if __name__ == '__main__':
    main()
