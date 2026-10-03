"""Small helper functions for opening and preparing the SQLite database."""

import sqlite3
from pathlib import Path

from models import (
    CREATE_CATEGORIES_TABLE,
    CREATE_EXPENSES_TABLE,
    CREATE_INCOMES_TABLE,
    CREATE_USERS_TABLE,
)

DATABASE_FILE = Path(__file__).parent / "expenses.db"


def get_connection():
    """Open the local database and return rows that work like dictionaries."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create tables and starter data; add user_id to an older expenses table."""
    with get_connection() as connection:
        connection.execute(CREATE_USERS_TABLE)
        connection.execute(
            "INSERT OR IGNORE INTO users (id, name) VALUES (1, 'Me')"
        )
        connection.execute(CREATE_CATEGORIES_TABLE)
        connection.execute(CREATE_EXPENSES_TABLE)

        # Older versions of this student project did not save an expense owner.
        expense_columns = connection.execute("PRAGMA table_info(expenses)").fetchall()
        if "user_id" not in [column["name"] for column in expense_columns]:
            connection.execute(
                "ALTER TABLE expenses ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1"
            )

        connection.execute(CREATE_INCOMES_TABLE)

        # Add a few useful categories only when they are not already present.
        starter_categories = [
            ("Food", "expense"), ("Travel", "expense"),
            ("Shopping", "expense"), ("Bills", "expense"),
            ("Education", "expense"), ("Health", "expense"),
            ("Other", "expense"), ("Salary", "income"),
            ("Gift", "income"), ("Other", "income"),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
            starter_categories,
        )
