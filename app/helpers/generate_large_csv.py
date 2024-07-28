import csv
import random
import os

def generate_large_csv(file_path, num_rows):
    songs = ["Song A", "Song B", "Song C", "Song D"]
    dates = ["2020-01-01", "2020-01-02"]

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Song", "Date", "Number of Plays"])
        
        for _ in range(num_rows):
            song = random.choice(songs)
            date = random.choice(dates)
            plays = random.randint(1, 1000)
            writer.writerow([song, date, plays])

# Generate a CSV with 1 million rows
output_path = os.path.join('data', 'large_example_input.csv')
generate_large_csv(output_path, 1000000)
