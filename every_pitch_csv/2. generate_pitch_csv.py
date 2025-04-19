import os
from typing import List
import csv
import tqdm
from at_bat.game_parser import GameParser

current_dir = os.path.dirname(os.path.abspath(__file__))
gamepk_csv_file_path = os.path.join(current_dir, 'gamepks.csv')
pitch_csv_file_path = os.path.join(current_dir, 'pitch.csv')

def start_csv():
    with open(pitch_csv_file_path, 'w', newline='', encoding='UTF-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=GameParser.field_names)
        writer.writeheader()

def read_gamepk_csv() -> List[int]:
    """
    Reads the gamepks from the gamepks.csv file and returns them as a
    list of integers

    Returns:
        List[int]: List of gamepks
    """
    gamepks: List[int] = []

    with open(gamepk_csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            gamepks.append(int(row[0]))

    return gamepks

def main():
    """
    Main function that creates a GameCSVCreator object for each gamepk
    """
    gamepks = read_gamepk_csv()
    # gamepks = [748542]
    # gamepks = get_daily_gamepks('2024-05-01')
    start_csv()
    for gamepk in tqdm.tqdm(gamepks):
        g = GameParser(gamepk)
        g.write_csv(pitch_csv_file_path, False)

if __name__ == '__main__':
    main()
