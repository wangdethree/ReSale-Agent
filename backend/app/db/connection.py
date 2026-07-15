from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.app.core.config import get_settings


def get_database_path() -> Path:
    settings = get_settings()
    db_path = settings.db_path
    if not db_path.is_absolute():
        db_path = settings.db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

