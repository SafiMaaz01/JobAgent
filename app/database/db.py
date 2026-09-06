import sqlite3
from pathlib import Path

DB_FILE = Path("data/jobs.db")


def get_connection():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_FILE)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

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

    # Add columns to existing databases created before
    # the approval and matcher-detail workflows were introduced.
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(jobs)")
    }

    if "review_status" not in columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN review_status TEXT DEFAULT 'pending'"
        )

    if "reviewed_at" not in columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN reviewed_at TEXT"
        )

    if "match_details" not in columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN match_details TEXT"
        )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()

    print("Database initialized successfully.")
    print(f"Database: {DB_FILE}")