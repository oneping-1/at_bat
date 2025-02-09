from typing import List, Tuple
from datetime import datetime, timedelta
from tqdm import tqdm
import csv

import matplotlib.pyplot as plt

from at_bat.statsapi_plus import get_daily_gamepks
from at_bat.umpire import Umpire

def get_gamepks(year) -> List[int]:
    start = datetime(year, 4, 1)
    end = datetime(year, 4, 30)

    all_gamepks: List[int] = []

    while start <= end:
        daily_gamepks: List[int] = get_daily_gamepks(start.strftime('%Y-%m-%d'))
        all_gamepks.extend(daily_gamepks)

        if start.day == 1:
            print(f'{start.strftime("%Y-%m-%d")}: {len(all_gamepks):>4d} games')
        start += timedelta(days=1)

    return all_gamepks

def analyze_umpires(gamepks: List[int]) -> Tuple[List[int], List[float], List[float]]:
    num_missed: List[int] = []
    home_favor: List[float] = []
    home_wpa: List[float] = []

    for gamepk in tqdm(gamepks):
        umpire = Umpire(gamepk=gamepk)
        umpire.calculate_game(method='monte')

        num_missed.append(umpire.num_missed_calls)
        home_favor.append(umpire.home_favor)
        home_wpa.append(umpire.home_wpa)

    return (num_missed, home_favor, home_wpa)

def send_to_csv(num_missed, home_favor, home_wpa):
    with open('umpire_favor_analysis.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for n, f, w in zip(num_missed, home_favor, home_wpa):
            writer.writerow([n, f, w])

def main():
    gamepks = get_gamepks(2024)

    num_missed, home_favor, home_wpa = analyze_umpires(gamepks)

    send_to_csv(num_missed, home_favor, home_wpa)

if __name__ == '__main__':
    main()
