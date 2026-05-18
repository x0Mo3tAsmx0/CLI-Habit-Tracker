from datetime import datetime
from functools import reduce

# =====================================================================
# PURE FUNCTIONAL HELPERS
# These functions do not mutate external state or touch the database.
# =====================================================================

def _parse_dates(date_strings):
    """
    Parses and sorts a list of timestamp strings into datetime objects.
    Ensures the event stream is in chronological order before reduction.
    """
    return sorted([datetime.strptime(d, '%Y-%m-%d %H:%M:%S') for d in date_strings])

def _streak_reducer(acc, current_date, periodicity):
    """
    Core reducer logic for dynamic streak calculation.
    Compares the current log date against the last recorded date in the accumulator,
    accounting for whether the habit requires daily or weekly completion.
    
    Returns the updated accumulator: (current_streak, max_streak, last_date)
    """
    current_streak, max_streak, last_date = acc
    
    if last_date is None:
        return (1, 1, current_date)
        
    delta = current_date - last_date
    
    if periodicity.lower() == 'daily':
        # Consecutive day continues streak; same day ignores it; gap breaks it.
        if delta.days == 1:
            new_streak = current_streak + 1
        elif delta.days == 0:
            new_streak = current_streak 
        else:
            new_streak = 1
    else: # Weekly
        # Check-off within 7 days continues streak; same day ignores it; gap breaks it.
        if 0 < delta.days <= 7:
            new_streak = current_streak + 1
        elif delta.days == 0:
            new_streak = current_streak
        else:
            new_streak = 1
            
    return (new_streak, max(max_streak, new_streak), current_date)

# =====================================================================
# CORE ANALYTICS MODULE
# Interfaces with the Database layer and applies functional processing.
# =====================================================================

def return_all_habits(db):
    """
    Fetches all habit metadata from the persistence layer.
    Returns a list of tuples containing (name, periodicity, created_at).
    """
    return db.fetch_data("SELECT name, periodicity, created_at FROM habits")

def return_habits_by_periodicity(db, periodicity):
    """
    Filters and retrieves habits directly from the database based on their tracking frequency.
    Uses parameterized querying to safely handle the user's periodicity input.
    """
    return db.fetch_data(
        "SELECT name, periodicity, created_at FROM habits WHERE periodicity COLLATE NOCASE = ?", 
        (periodicity,)
    )

def return_longest_streak_for_habit(db, habit_name, periodicity):
    """
    Retrieves a habit's entire event history and dynamically calculates its longest streak.
    Leverages functional reduction (reduce) to process the data stream without state mutation.
    """
    # Fetch raw timestamps from the tracker table
    logs = db.fetch_data("SELECT timestamp FROM tracker WHERE habit_name = ?", (habit_name,))
    
    # Extract the string from the tuple returned by SQLite
    log_dates = [row[0] for row in logs]
    
    if not log_dates:
        return 0
        
    parsed_dates = _parse_dates(log_dates)
    
    # Define the initial state for the reducer: (current, max, last_date)
    initial_state = (0, 0, None)
    
    # Inject the habit's periodicity into the generic reducer function
    reducer = lambda acc, date: _streak_reducer(acc, date, periodicity)
    
    # Execute the reduction and extract the max_streak
    final_state = reduce(reducer, parsed_dates, initial_state)
    return final_state[1]

def return_longest_streak_all(db):
    """
    Analyzes the entire database to find the habit with the highest overall streak.
    Uses map() to functionally process the streak calculation across all habits simultaneously.
    """
    habits = return_all_habits(db)
    if not habits:
        return ("None", 0)
        
    # Map each habit tuple to a new tuple containing its name and its calculated max streak
    streaks = list(map(
        lambda h: (h[0], return_longest_streak_for_habit(db, h[0], h[1])),
        habits
    ))
    
    # Return the tuple containing the absolute highest streak
    return max(streaks, key=lambda x: x[1])