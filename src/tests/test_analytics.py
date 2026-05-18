import pytest
from database import Database, setup_tables
import analytics

@pytest.fixture
def seeded_db():
    """Injects specific, hardcoded date edge-cases to test the analytics engine."""
    db = Database(":memory:")
    setup_tables(db)
    
    db.execute_query("INSERT INTO habits VALUES (?, ?, ?)", ("DailyTest", "Daily", "2024-01-01 00:00:00"))
    db.execute_query("INSERT INTO habits VALUES (?, ?, ?)", ("WeeklyTest", "Weekly", "2024-01-01 00:00:00"))
    
    # --- EDGE CASE 1: Leap Year & Broken Streak ---
    # Feb 28 to Mar 1 in 2024 (Leap Year) is 3 continuous days. 
    # Missing Mar 2 breaks the streak. Mar 3 and 4 starts a new streak of 2.
    daily_logs = [
        "2024-02-28 10:00:00", 
        "2024-02-29 10:00:00", # Leap Day!
        "2024-03-01 10:00:00", 
        # GAP: Missing 03-02
        "2024-03-03 10:00:00", 
        "2024-03-04 10:00:00"  
    ]
    for log in daily_logs:
        db.execute_query("INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)", ("DailyTest", log))
        
    # --- EDGE CASE 2: Weekly Gaps ---
    # Jan 1 to Jan 8 (7 days) -> Valid. Jan 8 to Jan 14 (6 days) -> Valid.
    # Gap until Feb 1 -> Streak broken. Max streak = 3.
    weekly_logs = [
        "2024-01-01 10:00:00",
        "2024-01-08 10:00:00",
        "2024-01-14 10:00:00",
        # GAP
        "2024-02-01 10:00:00"
    ]
    for log in weekly_logs:
        db.execute_query("INSERT INTO tracker (habit_name, timestamp) VALUES (?, ?)", ("WeeklyTest", log))
        
    return db

def test_return_all_habits(seeded_db):
    habits = analytics.return_all_habits(seeded_db)
    assert len(habits) == 2

def test_return_habits_by_periodicity(seeded_db):
    daily = analytics.return_habits_by_periodicity(seeded_db, "Daily")
    assert len(daily) == 1
    assert daily[0][0] == "DailyTest"

def test_longest_streak_daily_broken_and_leap_year(seeded_db):
    """Proves the reducer accurately handles leap years and broken daily streaks."""
    streak = analytics.return_longest_streak_for_habit(seeded_db, "DailyTest", "Daily")
    assert streak == 3  # The first streak of 3 is greater than the second streak of 2

def test_longest_streak_weekly(seeded_db):
    """Proves the reducer accurately calculates varying weekly frequencies."""
    streak = analytics.return_longest_streak_for_habit(seeded_db, "WeeklyTest", "Weekly")
    assert streak == 3

def test_return_longest_streak_all(seeded_db):
    """Proves the map() function correctly finds the highest streak globally."""
    best_habit, streak = analytics.return_longest_streak_all(seeded_db)
    # Both habits have a max streak of 3, so it should return 3
    assert streak == 3