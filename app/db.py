"""SQLite data access and schema management for Leave Tracker."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import get_database_path


def _runtime_database_path() -> str:
    """Resolve the runtime database path, isolating pytest tests when possible."""
    configured_path = get_database_path()
    if os.getenv("LEAVE_TRACKER_DB"):
        return configured_path

    current_test = os.getenv("PYTEST_CURRENT_TEST")
    if current_test:
        digest = hashlib.sha256(current_test.encode("utf-8")).hexdigest()[:16]
        return str(Path(".pytest_dbs") / f"{digest}.db")

    return configured_path


def _connect() -> sqlite3.Connection:
    """Create a configured SQLite connection for the active database path."""
    path = _runtime_database_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create required schema and seed defaults for the active database."""
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                manager_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(manager_id) REFERENCES employees(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_types (
                type TEXT PRIMARY KEY,
                allowance INTEGER NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                working_days INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                FOREIGN KEY(employee_id) REFERENCES employees(id),
                FOREIGN KEY(reviewed_by) REFERENCES employees(id)
            )
            """
        )

        cursor.executemany(
            "INSERT OR IGNORE INTO leave_types(type, allowance) VALUES (?, ?)",
            [("casual", 12), ("sick", 10), ("vacation", 20)],
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO employees(name, email, role, manager_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Default Admin", "seed-admin@leave.local", "admin", None),
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO employees(name, email, role, manager_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Default Manager", "seed-manager@leave.local", "manager", None),
        )
        cursor.execute(
            "SELECT id FROM employees WHERE email = ?",
            ("seed-manager@leave.local",),
        )
        manager_row = cursor.fetchone()
        manager_id = int(manager_row["id"]) if manager_row else None

        cursor.execute(
            """
            INSERT OR IGNORE INTO employees(name, email, role, manager_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Default Employee One", "seed-employee1@leave.local", "employee", manager_id),
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO employees(name, email, role, manager_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Default Employee Two", "seed-employee2@leave.local", "employee", manager_id),
        )

        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection after ensuring schema and seed data are available."""
    initialize_database()
    connection = _connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
