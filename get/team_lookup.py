import csv

def abv_from_id(code):
    with open('teams.csv') as file:
        reader = csv.reader(file)
        next(reader)

        for id, abv, div in reader:
            if code == int(id):
                return abv
            
def div_from_id(code):
    with open('teams.csv') as file:
        reader = csv.reader(file)
        next(reader)

        for id, abv, div in reader:
            if code == int(id):
                return div

if __name__ == '__main__':
    abv_from_id(140)