import csv
import logging
import os
from app.db import insert_record, fetch_sorted_data, init_db, clear_db
from uuid import uuid4
import threading

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def process_csv(input_file_path, output_file_path):
    """Processes the input CSV file and writes the aggregated results to the output CSV file."""
    try:
        logging.info(f"Starting processing of file: {input_file_path}")
        # Initialize and clear the database
        init_db()  # Ensure this is called to create the table
        clear_db() ## Clear any existing data in the table

        # Read the input CSV file and insert records into the database
        with open(input_file_path, mode='r', newline='') as input_file:
            csv_reader = csv.reader(input_file)
            header = next(csv_reader)  # Skip header
            for row in csv_reader:
                song, date, plays = row[0], row[1], int(row[2])
                insert_record(song, date, plays)
        logging.info(f"Inserted records from file: {input_file_path}")

        # Write the sorted data to the output CSV file in chunks
        with open(output_file_path, mode='w', newline='') as output_file:
            csv_writer = csv.writer(output_file)
            # Write header
            csv_writer.writerow(["Song", "Date", "Total Number of Plays for Date"])
            offset = 0
            limit = 500  # Fetch 500 records at a time
            while True:
                sorted_data = fetch_sorted_data(limit, offset)
                if not sorted_data:
                    break
                for song, date, total_plays in sorted_data:
                    csv_writer.writerow([song, date, total_plays])
                offset += limit
                logging.info(f"Fetched and wrote {offset} records to the output file")

        logging.info(f"Completed processing of file: {output_file_path}")
    except Exception as e:
        logging.error(f"Error processing CSV file: {e}")

def handle_file_upload(input_file, upload_folder):
    """Handles the uploaded file and starts the processing in a separate thread."""
    try:
        # Generate a unique task ID
        task_id = str(uuid4())
        # Define the input and output file paths
        input_file_path = os.path.join(upload_folder, f"{task_id}_input.csv")
        output_file_path = os.path.join(upload_folder, f"{task_id}_output.csv")

        # Save the uploaded file to the input file path
        with open(input_file_path, 'wb') as f:
            f.write(input_file.read())

        # Start a new thread to process the CSV file
        thread = threading.Thread(target=process_csv, args=(input_file_path, output_file_path))
        thread.start()

        return task_id
    except Exception as e:
        logging.error(f"Error handling file upload: {e}")
        return None

def get_result(task_id, upload_folder):
    """Returns the path to the processed file if it exists, otherwise None."""
    try:
        output_file_path = os.path.join(upload_folder, f"{task_id}_output.csv")
        logging.info(f"Checking for output file at: {output_file_path}")
        if os.path.exists(output_file_path):
            return output_file_path
        return None
    except Exception as e:
        logging.error(f"Error getting result for task {task_id}: {e}")
        return None
