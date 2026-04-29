"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Reusable SQLite connection and helper module.
               All DB access goes through here.
============================================================
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from core.src.runtime_paths import APP_DATA_DIR  

DB_PATH = Path(
    os.environ.get("DB_PATH", APP_DATA_DIR / "b")
)

def get_connection():
    """Open a connection to the SQLite DB with foreign keys enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction():
    """Context manager for a DB transaction. Commits on success, rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute(sql, params=()):
    """Run a single statement and return all rows as a list of dicts."""
    with transaction() as conn:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def execute_one(sql, params=()):
    """Run a single statement and return one row as a dict, or None."""
    with transaction() as conn:
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def insert(sql, params=()):
    """Run an INSERT and return the new row's ID."""
    with transaction() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid