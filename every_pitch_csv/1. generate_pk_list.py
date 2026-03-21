import os
from typing import List
import csv
import datetime
from at_bat.statsapi_plus import get_daily_gamepks

class Gamepk_finder:
    """Class to make a list of all gamepks from a given date range"""
    def __init__(self, start_date: str, end_date: str):
        self.gamepks: List = []
        self.start_date = datetime.date.fromisoformat(start_date)
        self.end_date = datetime.date.fromisoformat(end_date)

    def day_loop(self, date):
        """
        Gets the gamepks for a given date and adds them to the list. If
        the gamepk is already in the list, it will not be added.

        Args:
            date (str): Date in ISO 8601 format (YYYY-MM-DD)
        """
        daily_gamepks = get_daily_gamepks(date)

        for pk in daily_gamepks.copy():
            if pk in self.gamepks:
                daily_gamepks.remove(pk)

        self.gamepks += daily_gamepks
        print(f'{len(self.gamepks):4d}')

    def start(self):
        """Starts the loop from the start date to the end date"""
        date = self.start_date

        while date <= self.end_date:
            print(f'{date}:', end=' ')
            self.day_loop(date)
            date += datetime.timedelta(days=1)

    def save(self):
        """Saves the gamepks to a csv file"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(current_dir, 'gamepks.csv')

        with open(csv_file_path, 'a', newline='', encoding='UTF-8') as file:
            writer = csv.writer(file)

            for pk in self.gamepks:
                writer.writerow([pk])

if __name__ == '__main__':
    dates = [
        ('2017-04-02', '2017-10-01'),
        ('2018-03-29', '2018-10-01'),
        ('2019-03-28', '2019-09-29'),
        ('2020-07-23', '2020-09-27'),
        ('2021-04-01', '2021-10-03'),
        ('2022-04-07', '2022-10-05'),
        ('2023-03-30', '2023-10-01'),
        ('2024-03-28', '2024-09-30'),
        ('2025-03-27', '2025-09-28')
    ]

    for d in dates:
        finder = Gamepk_finder(start_date=d[0], end_date=d[1])
        finder.start()
        finder.save()
