"""Database dependencies for FastAPI endpoints."""
from typing import Generator
import sqlite3
from app.database.db import get_connection


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a database connection with sqlite3.Row factory and ensure it closes."""
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()
