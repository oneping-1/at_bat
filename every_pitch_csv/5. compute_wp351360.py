import itertools
import os
import csv
from typing import List, Tuple
import pandas as pd
from scipy.signal import convolve
from tqdm import tqdm

def read_re288() -> pd.DataFrame:
    """
    Read the re288.csv file and return it as a pandas DataFrame.

    Returns:
        pd.DataFrame: A pandas DataFrame with the contents of the re288.csv file.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 're288.csv')
    df = pd.read_csv(csv_file_path)

    for i in range(14):
        df[f'{i} runs'] = df[f'{i} runs'] / df['count']

    return df

def create_wp351360() -> List[dict]:
    """
    Create a dictionary with all possible states of a baseball game.
    Min and Max home lead is -30 and 30 respectively.

    Returns:
        List[dict]: A dictionary with all possible states of a baseball game.
    """
    balls = list(range(4))
    strikes = list(range(3))
    outs = list(range(3))
    is_first_base = [False, True]
    is_second_base = [False, True]
    is_third_base = [False, True]
    innings = list(range(1, 11)) # Extra innings is 10th inning
    is_top_inning = [True, False]
    home_lead = list(range(-30, 31))

    states = itertools.product(
        balls,
        strikes,
        outs,
        is_first_base,
        is_second_base,
        is_third_base,
        innings,
        is_top_inning,
        home_lead
    )

    # dict for speed
    wp351360 = {state: {'away_win': 0, 'home_win': 0, 'tie': 0} for state in states}

    print(len(wp351360))
    return wp351360

def calculate_win_probability(away_pmf: List[float], home_pmf: List[float], home_lead: int
                              ) -> Tuple[float, float, float]:
    """
    Calculate the win probability for the away team, home team, and a tie.

    Args:
        away_pmf (List[float]): Away team's PMF.
        home_pmf (List[float]): Home team's PMF.
        home_lead (int): Home team's lead.

    Returns:
        Tuple[float, float, float]: _description_
    """
    away_win_probability = 0
    home_win_probability = 0
    tie_probability = 0

    for a in range(14):
        for h in range(14):
            if a > (h + home_lead):
                away_win_probability += away_pmf[a] * home_pmf[h]
            elif (h + home_lead) > a:
                home_win_probability += away_pmf[a] * home_pmf[h]
            else:
                tie_probability += away_pmf[a] * home_pmf[h]

    return (away_win_probability, home_win_probability, tie_probability)

def calculate_half_inning_pmf(re288: pd.DataFrame, state: tuple) -> List[float]:
    """
    Calculate the PMF for a half inning.

    Args:
        re288 (pd.DataFrame): Run expectancy DataFrame.
        state (tuple): The state of the game.

    Returns:
        List[float]: The PMF for the half inning.
    """
    re288_state = re288[
        (re288['balls'] == state[0]) &
        (re288['strikes'] == state[1]) &
        (re288['outs'] == state[2]) &
        (re288['is_first_base'] == state[3]) &
        (re288['is_second_base'] == state[4]) &
        (re288['is_third_base'] == state[5])
    ]

    x = re288_state.loc[:, '0 runs':'13 runs'].values.tolist()[0]
    return x

def calculate_wp351360(re288: pd.DataFrame, wp351360: List[dict]) -> List[dict]:
    """
    Calculate the win probability for all possible states of a baseball game.

    Args:
        re288 (pd.DataFrame): Run expectancy DataFrame.
        wp316224 (List[dict]): Dictionary with all possible states of a
            baseball game.

    Returns:
        List[dict]: Dictionary with all possible states of a baseball
            game and their win probabilities
    """
    for state, _ in tqdm(wp351360.items()):
        new_inning_pmf = calculate_half_inning_pmf(re288, (0, 0, 0, False, False, False))
        extra_inning_pmf = calculate_half_inning_pmf(re288, (0, 0, 0, False, True, False))

        # if (state[7] is False) and (state[6] == 9) and (state[8] > 0):
        #    print(state)

        # Get PMFs for the current inning
        is_top_inning = state[7]
        if is_top_inning is True:
            away_pmf = calculate_half_inning_pmf(re288, state)
            home_pmf = new_inning_pmf.copy()
        else:
            away_pmf = [1] + [0] * 13
            home_pmf = calculate_half_inning_pmf(re288, state)

        # Calculate the PMFs for the rest of the game
        inning = state[6]
        for _ in range(inning + 1, 10):
            away_pmf = convolve(away_pmf, new_inning_pmf)
            home_pmf = convolve(home_pmf, new_inning_pmf)

        if inning > 9:
            if is_top_inning is True:
                away_pmf = calculate_half_inning_pmf(re288, state)
                home_pmf = extra_inning_pmf.copy()
            elif is_top_inning is False:
                away_pmf = [1] + [0] * 13
                home_pmf = calculate_half_inning_pmf(re288, state)

        away, home, tie = calculate_win_probability(away_pmf, home_pmf, state[8])
        wp351360[state] = {'away_win': away, 'home_win': home, 'tie': tie}

    return wp351360

def write_wp351360(wp351360: List[dict]):
    """
    Write the win probability matrix to a CSV file.

    Args:
        wp311040 (List[dict]): The win probability matrix.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 'wp351360.csv')

    with open(csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        field_names = [
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

        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for key, value in wp351360.items():
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
    """
    Main function to calculate the win probability matrix.
    """
    re288 = read_re288()
    wp351360 = create_wp351360()
    wp351360 = calculate_wp351360(re288, wp351360)
    write_wp351360(wp351360)
    for key, value in wp351360.items():
        print(key, value)

if __name__ == '__main__':
    main()
