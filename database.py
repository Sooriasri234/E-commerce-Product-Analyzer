import sqlite3
from pathlib import Path

from deployment.app_config import DB_PATH


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                provider TEXT NOT NULL DEFAULT 'local',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                positive_rate REAL NOT NULL,
                avg_rating REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )


def create_user(name: str, email: str, password_hash: str | None, provider: str = "local") -> int:
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, provider) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, provider),
        )
        return int(cursor.lastrowid)


def create_google_user(name: str, email: str) -> int:
    return create_user(name, email, None, provider="google")


def get_user_by_email(email: str):
    with connect() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def record_analysis_run(user_id: int, file_name: str, row_count: int, positive_rate: float, avg_rating: float) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO analysis_runs (user_id, file_name, row_count, positive_rate, avg_rating)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, file_name, row_count, positive_rate, avg_rating),
        )


def get_recent_runs(user_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT file_name, row_count, positive_rate, avg_rating, created_at
            FROM analysis_runs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 8
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
