import pytest
from database import Database, setup_tables
from habit import Habit

@pytest.fixture
def test_db():
    db = Database(":memory:")
    setup_tables(db)
    return db

def test_habit_creation_and_storage(test_db):
    """Tests if a Habit object correctly persists its state to the DB."""
    h = Habit("Drink Water", "Daily", test_db)
    assert h.store() is True
    
    result = test_db.fetch_data("SELECT name FROM habits WHERE name = 'Drink Water'")
    assert len(result) == 1

def test_habit_check_off(test_db):
    """Tests if the object successfully generates and logs a tracker timestamp."""
    h = Habit("Run", "Weekly", test_db)
    h.store()
    assert h.check_off() is True
    
    logs = test_db.fetch_data("SELECT * FROM tracker WHERE habit_name = 'Run'")
    assert len(logs) == 1

def test_habit_delete_cascades(test_db):
    """
    Crucial Test: Verifies that deleting a habit automatically wipes its tracking 
    logs due to the ON DELETE CASCADE constraint.
    """
    h = Habit("Read", "Daily", test_db)
    h.store()
    h.check_off()
    
    # Execute deletion
    assert h.delete() is True
    
    # Verify both the habit and its orphaned logs are gone
    assert len(test_db.fetch_data("SELECT * FROM habits WHERE name = 'Read'")) == 0
    assert len(test_db.fetch_data("SELECT * FROM tracker WHERE habit_name = 'Read'")) == 0