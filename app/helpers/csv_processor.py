import csv 
from collections import defaultdict
import os
from uuid import uuid4
import threading

def process_csv(input_file_path, output_file_path):
    song_data = defaultdict(lambda: defaultdict(int))

    with open(input_file_path, mode='r', newline='') as input_file:
        csv_reader = csv.reader(input_file)
        header = next(csv_reader)  # Skip header
        for row in csv_reader:
            song, date, plays = row[0], row[1], int(row[2])
            song_data[song][date] += plays

    sorted_data = sorted(
        ((song, date, plays) for song, dates in song_data.items() for date, plays in dates.items()),
        key=lambda x: (x[0], x[1])
    )

    with open(output_file_path, mode='w', newline='') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(["Song", "Date", "Total Number of Plays for Date"])
        for song, date, total_plays in sorted_data:
            csv_writer.writerow([song, date, total_plays])

def handle_file_upload(input_file):
    task_id = str(uuid4())
    input_file_path = f"{task_id}_input.csv"
    output_file_path = f"{task_id}_output.csv"

    with open(input_file_path, 'wb') as f:
        f.write(input_file.read())

    thread = threading.Thread(target=process_csv, args=(input_file_path, output_file_path))
    thread.start()

    return task_id

def get_result(task_id):
    output_file_path = f"{task_id}_output.csv"
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as f:
            return f.read()
    return None

if __name__ == "__main__":
    with open('example_input.csv', 'rb') as input_file:
        task_id = handle_file_upload(input_file)
        print(f"Task ID: {task_id}")

    import time
    while True:
        result = get_result(task_id)
        if result:
            print(f"Processed Output:\n{result}")
            break
        else:
            print("Processing...")
            time.sleep(1)