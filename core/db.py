import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(defaults: dict | None = None):
    """Crée les tables si besoin et seed la config avec les valeurs par défaut manquantes."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

        if defaults:
            existing_keys = {row["key"] for row in conn.execute("SELECT key FROM config")}
            now = datetime.now(timezone.utc).isoformat()
            for key, value in defaults.items():
                if key not in existing_keys:
                    conn.execute(
                        "INSERT INTO config (key, value, updated_at) VALUES (?, ?, ?)",
                        (key, json.dumps(value), now),
                    )


def get_config_value(key: str, default=None):
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])


def get_all_config() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM config").fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}


def set_config_value(key: str, value):
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO config (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, json.dumps(value), now),
        )


def create_user(username: str, password_hash: str, is_admin: bool = False):
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, int(is_admin), now),
        )


def get_user(username: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def list_users() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, username, is_admin, created_at FROM users").fetchall()
        return [dict(row) for row in rows]


def delete_user(username: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        return cursor.rowcount > 0


def count_users() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
