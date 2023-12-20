import os
import requests

def get_ip() -> str:
    """
    Gets the current ip address of the ESP32 from ip.txt
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(current_dir, '..', 'csv')
    csv_file_path = os.path.join(csv_dir, 'ip.txt')

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        ip = file.read()

    return ip

def main():
    ip = get_ip()

    games = []

    games.append({
        'away_abv': 'AZ',
        'home_abv': 'TEX',
        'away_score': 5,
        'home_score': 3,
        'inning': 9,
        'inning_state': 'B',
        'outs': 1,
        'runners': 1,
        'game_state': 'L'
    })

    games.append({
        'away_abv': 'TEX',
        'home_abv': 'AZ',
        'away_score': 5,
        'home_score': 0,
        'inning': 9,
        'inning_state': 'B',
        'outs': 3,
        'runners': 0,
        'game_state': 'F'
    })

    games.append({
        'away_abv': 'CHC',
        'home_abv': 'TEX',
        'away_score': 0,
        'home_score': 0,
        'inning': 1,
        'inning_state': 'T',
        'outs': 0,
        'runners': 0,
        'game_state': 'P',
        'start_time': '6:35'
    })

    for i, game in enumerate(games):
        response = requests.get(f'http://{ip}:8080/{i}', timeout=10, params=game)

        if response.status_code != 200:
            print(f'Error: {response.status_code} {response.reason}')

        print(response.url)

if __name__ == '__main__':
    main()
