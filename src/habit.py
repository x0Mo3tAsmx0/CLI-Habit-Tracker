import sqlite3
from datetime import datetime

class Habit:
    """
    The OOP representation of a Habit.
    Encapsulates the habit's state (name, frequency, creation time) and 
    delegates all database lifecycle operations to the persistence layer.
    """
    def __init__(self, name, periodicity, db, creation_date=None):
        self.name = name
        self.periodicity = periodicity
        self.db = db
        # Set to the provided date (when loading from the database), 
        # or default to the current time (when creating a brand new habit).
        self.creation_date = creation_date or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def store(self):
        """
        Persists the habit's initial metadata to the database.
        Gracefully catches duplicate name attempts without exposing SQL errors.
        """
        try:
            self.db.execute_query(
                "INSERT INTO habits (name, periodicity, created_at) VALUES (?, ?, ?)",
                (self.name, self.periodicity, self.creation_date)
            )
            return True
        except sqlite3.IntegrityError:
            # Cleanly handle the UNIQUE constraint failure
            print(f"[!] A habit named '{self.name}' already exists. Please choose a different name.\n")
            return False
        except Exception:
            # Fallback that completely hides internal implementation details
            print("[!] An unexpected internal error occurred while saving the habit.\n")
            return False

    def check_off(self):
        """
        Records a completion event for this habit.
        Automatically generates a high-fidelity timestamp and logs it to the tracker table.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.db.execute_query(
                "INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)",
                (self.name, timestamp)
            )
            return True
        except Exception as e:
            print(f"Error checking off habit: {e}")
            return False

    def delete(self):
        """
        Removes the habit record from the main table. 
        Relies on the SQLite ON DELETE CASCADE constraint to automatically 
        sweep and delete all associated logs in the tracker table.
        """
        try:
            self.db.execute_query("DELETE FROM habits WHERE name = ?", (self.name,))
            return True
        except Exception as e:
            print(f"Error deleting habit: {e}")
            return False