import pytest
from database import Database, setup_tables

@pytest.fixture
def test_db():
    """Spins up an isolated, temporary in-memory database for testing."""
    db = Database(":memory:")
    setup_tables(db)
    return db

def test_database_initialization(test_db):
    """Verifies that the schema successfully creates both normalized tables."""
    tables = test_db.fetch_data("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t[0] for t in tables]
    
    assert "habits" in table_names
    assert "tracker" in table_names

def test_execute_and_fetch(test_db):
    """Verifies the core UML methods can write and read data safely."""
    test_db.execute_query(
        "INSERT INTO habits (name, periodicity, created_at) VALUES (?, ?, ?)", 
        ("DB Test", "Daily", "2026-01-01 12:00:00")
    )
    result = test_db.fetch_data("SELECT * FROM habits WHERE name = ?", ("DB Test",))
    
    assert len(result) == 1
    assert result[0][0] == "DB Test"