"""Database dependencies for FastAPI endpoints."""
from typing import Generator
import sqlite3
from app.database.db import DB_FILE


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a per-request database connection safe across worker threads."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_FILE, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
