# CSV Processor and API for Large File Handling

This project consists of three main components:
1. A CSV processing module that processes large CSV files and generates output CSV files.
2. An API that allows users to upload CSV files for processing and retrieve the results asynchronously.
3. A script to generate large CSV files for testing purposes.

## Project Structure

```
BMAT Music Assignment/
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── db.py  # Database setup and helper functions
│   ├── tasks.py
│   ├── utils.py
├── helpers/
│   ├── csv_processor.py
│   ├── generate_large_csv.py
├── data/
│   ├── example_input.csv  # Provided example input
│   ├── large_example_input.csv  # Generated large input
├── templates/
│   └── index.html  # HTML template for the home page
├── uploads/  # This is where the uploaded and processed files will be stored
│   └── csv_data.db  # SQLite database file created during processing
├── interview.txt
├── README.md
├── requirements.txt
├── run.py
```

## Requirements

- Python 3.x
- Flask

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd BMAT Music Assignment
   ```

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Initialize the database**:
   Run the Flask server to initialize the database.
   ```bash
   python run.py
   ```

   Ensure the `uploads/` directory exists and contains the `csv_data.db` file after the server starts.

2. **Start the Flask server**:
   ```bash
   python run.py
   ```

   The server will start and listen on `http://127.0.0.1:5000`.

## API Endpoints

### 1. Upload File for Processing

- **Endpoint**: `/upload`
- **Method**: POST
- **Description**: Uploads a CSV file for processing. The file is processed asynchronously.
- **Request**: The request should contain a file.
- **Response**: Returns a `task_id` which can be used to retrieve the processing result.

#### Example Request
```bash
curl -X POST -F "file=@/path/to/your/file.csv" http://localhost:5000/upload
```

#### Example Response
```json
{
  "task_id": "some-unique-task-id"
}
```

### 2. Retrieve Processing Result

- **Endpoint**: `/result/<task_id>`
- **Method**: GET
- **Description**: Retrieves the processed CSV file using the `task_id`.
- **Response**: Returns the processed CSV file if processing is complete, otherwise returns a status indicating that the file is still processing or not found.

#### Example Request
```bash
curl http://localhost:5000/result/some-unique-task-id
```

## Detailed Code Explanation

### `app/app.py`

```python
from flask import Flask, request, jsonify, send_file, render_template
import os
import logging
from app.utils import process_csv, handle_file_upload, get_result

# Initialize Flask application
app = Flask(__name__, template_folder='../templates')
# Configure the folder for file uploads
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/', methods=['GET', 'POST'])
def home():
    """Renders the home page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload and starts processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            logging.info(f"File uploaded: {file.filename}")
            task_id = handle_file_upload(file, app.config['UPLOAD_FOLDER'])
            logging.info(f"Task ID generated: {task_id}")
            return jsonify({'task_id': task_id}), 202
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        return jsonify({'error': 'An error occurred during file upload'}), 500

@app.route('/result/<task_id>', methods=['GET'])
def get_file_result(task_id):
    """Retrieves the processed file based on the task ID."""
    try:
        result = get_result(task_id, app.config['UPLOAD_FOLDER'])
        if result:
            return send_file(result)
        return jsonify({'status': 'Processing or not found'}), 404
    except Exception as e:
        logging.error(f"Error retrieving result for task {task_id}: {e}")
        return jsonify({'error': 'An error occurred while retrieving the result'}), 500

if __name__ == '__main__':
    # Run the Flask application in debug mode
    app.run(debug=True)
```

### `app/utils.py`

This file contains the `process_csv` function which processes the CSV file.

```python
import csv
import logging
import os
from app.db import insert_record, fetch_sorted_data, init_db, clear_db

def process_csv(input_file_path, output_file_path):
    """Processes the input CSV file and writes the aggregated results to the output CSV file."""
    try:
        logging.info(f"Starting processing of file: {input_file_path}")
        # Initialize and clear the database
        init_db()  # Ensure this is called to create the table
        clear_db()  # Clear any existing data in the table

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

# Computational Complexity: O(n log n)
# - Reading and inserting records into the database: O(n)
# - Fetching and sorting data from the database: O(n log n)
# - Writing sorted data to output file: O(n)
# Overall complexity is dominated by the sorting step: O(n log n)
```

### `app/db.py`

This file contains the database setup and helper functions. The database file (`csv_data.db`) is created when the application starts processing a CSV file.

```python
import sqlite3
import

 logging

def get_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('uploads/csv_data.db')
    return conn

def init_db():
    """Initializes the database by creating the necessary table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song TEXT NOT NULL,
            date TEXT NOT NULL,
            plays INTEGER NOT NULL
        )
    ''')
    conn.commit()
    logging.info("Database initialized and table created.")
    cursor.close()
    conn.close()

def clear_db():
    """Clears the database by deleting all records in the plays table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM plays')
    conn.commit()
    logging.info("Database cleared.")
    cursor.close()
    conn.close()

def insert_record(song, date, plays):
    """Inserts a record into the plays table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO plays (song, date, plays) VALUES (?, ?, ?)', (song, date, plays))
    conn.commit()
    logging.info(f"Inserted record: ({song}, {date}, {plays})")
    cursor.close()
    conn.close()

def fetch_sorted_data(limit, offset):
    """Fetches sorted data from the plays table in chunks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT song, date, SUM(plays) as total_plays
        FROM plays
        GROUP BY song, date
        ORDER BY song, date
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    results = cursor.fetchall()
    logging.info(f"Fetched {len(results)} records from database.")
    cursor.close()
    conn.close()
    return results

# Computational Complexity:
# - init_db: O(1)
# - insert_record: O(1) for each insert, O(n) for n records
# - fetch_sorted_data: O(n log n) due to the sorting step
# - clear_db: O(1)
```

### `helpers/csv_processor.py`

This file contains core functions for handling CSV file processing and managing tasks.

```python
import csv
from collections import defaultdict
import os
from uuid import uuid4
import threading

def process_csv(input_file_path, output_file_path):
    """Processes the input CSV file and writes the aggregated results to the output CSV file."""
    song_data = defaultdict(lambda: defaultdict(int))

    # Read the input CSV file and aggregate data
    with open(input_file_path, mode='r', newline='') as input_file:
        csv_reader = csv.reader(input_file)
        header = next(csv_reader)  # Skip header
        for row in csv_reader:
            song, date, plays = row[0], row[1], int(row[2])
            song_data[song][date] += plays

    # Create a sorted list of tuples (song, date, total_plays)
    sorted_data = sorted(
        ((song, date, plays) for song, dates in song_data.items() for date, plays in dates.items()),
        key=lambda x: (x[0], x[1])
    )

    # Write the aggregated results to the output CSV file
    with open(output_file_path, mode='w', newline='') as output_file:
        csv_writer = csv.writer(output_file)
        # Write header
        csv_writer.writerow(["Song", "Date", "Total Number of Plays for Date"])
        for song, date, total_plays in sorted_data:
            csv_writer.writerow([song, date, total_plays])

def handle_file_upload(input_file):
    """Handles the uploaded file and starts the processing in a separate thread."""
    task_id = str(uuid4())
    input_file_path = f"uploads/{task_id}_input.csv"
    output_file_path = f"uploads/{task_id}_output.csv"

    # Save the uploaded file to the input file path
    with open(input_file_path, 'wb') as f:
        f.write(input_file.read())

    # Start a new thread to process the CSV file
    thread = threading.Thread(target=process_csv, args=(input_file_path, output_file_path))
    thread.start()

    return task_id

def get_result(task_id):
    """Returns the path to the processed file if it exists, otherwise None."""
    output_file_path = f"uploads/{task_id}_output.csv"
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as f:
            return f.read()
    return None

if __name__ == "__main__":
    # Example usage: upload and process a CSV file
    with open('data/example_input.csv', 'rb') as input_file:
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

# Computational Complexity:
# - process_csv: O(n log n)
# - handle_file_upload: O(1)
# - get_result: O(1) for checking file existence
```

### `helpers/generate_large_csv.py`

This file contains a script to generate large CSV files for testing purposes.

```python
import csv
import random

def generate_large_csv(file_path, num_rows):
    """Generates a large CSV file with random data for testing."""
    songs = ["Song A", "Song B", "Song C", "Song D"]
    start_date = 20200101

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Song", "Date", "Number of Plays"])
        
        for _ in range(num_rows):
            song = random.choice(songs)
            date = start_date + random.randint(0, 30)  # Random date in January 2020
            plays = random.randint(1, 1000)
            writer.writerow([song, str(date), plays])

# Generate a CSV with 1 million rows
generate_large_csv('data/large_example_input.csv', 1000000)

# Computational Complexity: O(n)
# - Writing num_rows records to the file: O(n)
```

## Testing the Application

### Run Flask Server

1. **Run Flask Server**:
   ```bash
   python run.py
   ```

2. **Upload File Using Curl**:
   Open a new terminal and run the following command (replace the file path with the absolute path to your CSV file):

   Using `localhost`:
   ```bash
   curl -X POST -F "file=@D:/BMAT Music Assignment/data/example_input.csv" http://localhost:5000/upload
   ```

   Using `127.0.0.1`:
   ```bash
   curl -X POST -F "file=@D:/BMAT Music Assignment/data/example_input.csv" http://127.0.0.1:5000/upload
   ```

   Both commands will send a POST request to the API with the file attached.

   The response should look like this:
   ```json
   {
     "task_id": "some-unique-task-id"
   }
   ```

3. **Check the Result Using Curl**:
   Use the `task_id` from the previous response to check the result:

   ```bash
   curl http://localhost:5000/result/some-unique-task-id
   ```

4. **Generate a Large CSV File for Testing**:
   Open a terminal and run the following command to generate a large CSV file:

   ```bash
   python app/helpers/generate_large_csv.py
   ```

   This will create a file named `large_example_input.csv` in your `data` directory.

5. **Upload the Large CSV File Using Curl**:
   ```bash
   curl -X POST -F "file=@D:/BMAT Music Assignment/data/large_example_input.csv" http://localhost:5000/upload
   ```

### Verify the SQLite Database

1. **Check the Database Using SQLite Command-Line Tool**:
   ```bash
   sqlite3 uploads/csv_data.db
   ```

2. **List the Tables**:
   ```sql
   .tables
   ```

3. **Check the Schema of the `plays` Table**:
   ```sql
   .schema plays
   ```

4. **Query the Data in the `plays` Table**:
   ```sql
   SELECT * FROM plays;
   ```

5. **Fetch Sorted Data**:
   ```sql
   SELECT song, date, SUM(plays) as total_plays
   FROM plays
   GROUP BY song, date
   ORDER BY song, date;
   ```

6. **Exit the SQLite Command-Line Tool**:
   ```sql
   .exit
   ```

### Verifying with DB Browser for SQLite (Optional)

1. **Download and install DB Browser for SQLite** from [here](https://sqlitebrowser.org/).

2. **Open DB Browser for SQLite**.

3. **Open the database file** (`uploads/csv_data.db`) from your project directory.

4. **Verify the Table and Data**:
   - Go to the `Database Structure` tab to see the `plays` table.
   - Go to the `Browse Data` tab to see the records in the `plays` table.
   - Run custom SQL queries using the `Execute SQL` tab.

## Additional Considerations

- **Error Handling**: Ensure robust error handling in your code to

 manage potential issues during file upload and processing.
- **Concurrency**: The use of threading allows for concurrent processing of multiple file uploads. Ensure that your server can handle the concurrency without performance degradation.
- **Security**: Validate file uploads to prevent security vulnerabilities such as uploading malicious files.

## Assignment Rules

### Code Explanation

**CSV Processing Module:**
- **Reading CSV:** Reads the input CSV file line by line to handle large files that may exceed memory.
- **Database Insertion:** Each record is inserted into an SQLite database to manage large datasets efficiently.
- **Data Aggregation:** Data is fetched from the database and aggregated by song and date, then sorted before being written to the output CSV file.

**API and Asynchronous Task Processing:**
- **File Upload:** Handles file uploads and initiates CSV processing in a separate thread to allow the API to handle further requests.
- **Task ID:** Generates a unique task ID for each file upload to track processing.
- **Result Retrieval:** Allows users to retrieve the processed file using the task ID.

### Background Implementation for Production

The current implementation uses Flask and SQLite for simplicity and can be deployed to production with some modifications:
- **Web Server:** Use a production-grade WSGI server like Gunicorn to serve the Flask application.
- **Database:** Consider using a more robust database like PostgreSQL for better scalability and reliability.
- **Asynchronous Task Queue:** Implement a task queue using Celery or RQ for more efficient background processing and better task management.

## Configuration and Instructions for Starting the Project

1. **Clone the Repository:**
   ```bash
   git clone <repository_url>
   cd BMAT Music Assignment
   ```

2. **Create a Virtual Environment and Activate It:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the Required Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask Server:**
   ```bash
   python run.py
   ```

5. **Upload a CSV File Using Curl:**
   ```bash
   curl -X POST -F "file=@D:/BMAT Music Assignment/data/example_input.csv" http://localhost:5000/upload
   ```

6. **Check the Result Using Curl:**
   ```bash
   curl http://localhost:5000/result/some-unique-task-id
   ```

## Computational Complexity

### CSV Processing Module
- **Reading CSV:** O(n)
- **Database Insertion:** O(n)
- **Data Aggregation and Sorting:** O(n log n)
- **Writing Output CSV:** O(n)

### Database Operations
- **Initialize Database:** O(1)
- **Insert Record:** O(1) per insert, O(n) for n records
- **Fetch Sorted Data:** O(n log n)
- **Clear Database:** O(1)