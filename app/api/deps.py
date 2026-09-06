"""
Database dependencies and connection lifecycle for FastAPI endpoints.

Provides a per-request SQLite connection dependency `get_db` using FastAPI's dependency injection.
- Ensures the data directory exists before connecting.
- Sets `check_same_thread=False` to allow FastAPI worker threads to use the connection safely.
- Sets `connection.row_factory = sqlite3.Row` to allow dictionary-like and name-based column access.
- Ensures connections are automatically closed when the HTTP request finishes (in the `finally` block).
"""
from typing import Generator
import sqlite3
from app.database.db import DB_FILE


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Yield a scoped SQLite database connection for the duration of a request.
    Closes the connection deterministically when the request response is returned.
    """
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False is essential for FastAPI async/threadpool request handlers
    connection = sqlite3.connect(DB_FILE, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
