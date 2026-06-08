import sqlite3
import os
from pathlib import Path

DEFAULT_DATABASE_PATH = Path("data") / "applications.db"


def get_database_path() -> Path:
    return Path( os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH) )


def get_connection() -> sqlite3.Connection:
    database_path = get_database_path()
    database_path.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection
  

def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS application_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                match_score INTEGER NOT NULL,
                seniority_signal TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )