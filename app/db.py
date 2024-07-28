import sqlite3
import logging

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
