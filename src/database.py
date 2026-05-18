import sqlite3
from datetime import datetime, timedelta

class Database:
    """
    Manages the SQLite database connection.
    Provides a simplified, encapsulated interface for the application to interact
    with the database without needing to write boilerplate connection logic everywhere.
    """
    def __init__(self, db_name="habits.db"):
        self.conn = sqlite3.connect(db_name)
        # SQLite disables foreign keys by default. We enable them here to ensure 
        # relational integrity (e.g., deleting a habit safely cascades to its tracker logs).
        self.execute_query("PRAGMA foreign_keys = 1")

    def execute_query(self, query, params=()):
        """
        Executes write operations (INSERT, UPDATE, DELETE) or schema changes.
        Uses parameterized queries (params) to safely handle variable data and prevent injection.
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetch_data(self, query, params=()):
        """
        Executes read operations (SELECT) and returns the fetched records.
        Returns a list of tuples representing the rows from the database.
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


# =====================================================================
# SYSTEM INITIALIZATION & MOCK DATA
# =====================================================================

def setup_tables(db):
    """
    Initializes the relational database schema. 
    Creates the 'habits' table for metadata and the 'tracker' table for event logs.
    """
    db.execute_query('''
        CREATE TABLE IF NOT EXISTS habits (
            name TEXT PRIMARY KEY,
            periodicity TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    db.execute_query('''
        CREATE TABLE IF NOT EXISTS tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_name TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (habit_name) REFERENCES habits (name) ON DELETE CASCADE
        )
    ''')

def seed_db(db):
    """
    Injects a predefined 28-day historical dataset if the database is empty.
    This provides immediate mock data to test the functional analytics module.
    """
    count = db.fetch_data("SELECT COUNT(*) FROM habits")[0][0]
    
    # Only seed if the database is completely empty
    if count == 0:
        print("Initializing database with 4-week test fixture...")
        now = datetime.now()
        start_date = now - timedelta(days=28)
        
        # 1. Insert base habits with their tracking periodicity
        habits_data = [
            ("Drink Water", "Daily", start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ("Go for a Run", "Weekly", start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ("Read a Book", "Daily", start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ("Learn Python", "Daily", start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ("Clean Apartment", "Weekly", start_date.strftime('%Y-%m-%d %H:%M:%S'))
        ]
        for data in habits_data:
            db.execute_query("INSERT INTO habits VALUES (?, ?, ?)", data)
        
        # 2. Generate historical check-off logs mimicking real-world behavior
        for i in range(28):
            current_date = start_date + timedelta(days=i)
            timestamp_str = current_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Perfect 28-day streak
            db.execute_query("INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)", ("Drink Water", timestamp_str))
            
            # Daily habit with occasional missed days (creates intentional broken streaks)
            if i % 5 != 0:
                db.execute_query("INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)", ("Read a Book", timestamp_str))
                
            # Daily habit skipping weekends
            if current_date.weekday() < 5:
                db.execute_query("INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)", ("Learn Python", timestamp_str))
                
            # Weekly habits checked off exactly once every 7 days
            if i % 7 == 0:
                db.execute_query("INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)", ("Go for a Run", timestamp_str))
                db.execute_query("INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)", ("Clean Apartment", timestamp_str))
        
        print("Mock data successfully seeded.")