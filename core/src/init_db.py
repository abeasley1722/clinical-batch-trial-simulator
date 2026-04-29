"""
============================================================
Author:        Jared Garcia
Date Created:  2026-03-22
Description:   Initializes the SQLite database and creates
               all tables from scratch. Safe to run multiple
               times — uses CREATE TABLE IF NOT EXISTS.

Usage:
    python core/src/init_db.py
============================================================
"""

from core.src.database.connection import get_connection, DB_PATH
from core.src.database.schema import ALL_TABLES

def init_db():
    print(f"Initializing database at: {DB_PATH}")
    conn = get_connection()
    try:
        for statement in ALL_TABLES:
            conn.execute(statement)
        conn.commit()
        print("All tables created successfully.")
    finally:
        conn.close()