"""Database initialization and connection management for JobAgent.

This module provides the core SQLite database connection factory and ensures
that the jobs table is created with all required columns, indices, and schema
migrations for job matching, human reviews, and application tracking.
"""
import sqlite3
from pathlib import Path

# Path to the primary SQLite database file
DB_FILE = Path("data/jobs.db")


def get_connection() -> sqlite3.Connection:
    """
    Open and return a new SQLite database connection with row factory configured.
    
    Ensures that parent directories (data/) exist before connecting.
    Configures row_factory = sqlite3.Row so query results can be accessed
    both by column index and by case-insensitive column name.
    """
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_FILE)

    # Return rows as dictionary-like Row objects
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """
    Initialize the SQLite database schema and apply non-destructive column migrations.
    
    Creates the 'jobs' table if it does not already exist, and checks for columns
    introduced in later iterations (review_status, reviewed_at, match_details)
    to safely upgrade older databases without losing data.
    """
    connection = get_connection()

    # Create master jobs table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            source TEXT NOT NULL,
            external_id TEXT NOT NULL,

            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,

            url TEXT NOT NULL,
            description TEXT,

            posted_at TEXT,
            updated_at TEXT,

            is_relevant INTEGER DEFAULT 0,

            match_score INTEGER,
            recommendation TEXT,

            matched_at TEXT,
            match_details TEXT,

            review_status TEXT DEFAULT 'pending',
            reviewed_at TEXT,

            applied_at TEXT,

            UNIQUE(source, external_id)
        )
    """)

    # Non-destructive schema migrations:
    # Add columns to existing databases created before the approval
    # and matcher-detail workflows were introduced.
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(jobs)")
    }

    # Add review_status column if missing
    if "review_status" not in columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN review_status TEXT DEFAULT 'pending'"
        )

    # Add reviewed_at timestamp column if missing
    if "reviewed_at" not in columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN reviewed_at TEXT"
        )

    # Add match_details JSON column if missing
    if "match_details" not in columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN match_details TEXT"
        )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    # When executed directly (e.g. `python -m app.database.db`), run initialization
    initialize_database()

    print("Database initialized successfully.")
    print(f"Database: {DB_FILE}")