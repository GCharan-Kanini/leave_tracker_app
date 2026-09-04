"""Configuration helpers for Leave Tracker."""

from __future__ import annotations

import os


DEFAULT_DATABASE_PATH = "leave_tracker.db"


def get_database_path() -> str:
    """Return the SQLite database path from environment configuration.

    Returns:
        The configured database path from ``LEAVE_TRACKER_DB`` when present,
        otherwise ``leave_tracker.db``.
    """
    return os.getenv("LEAVE_TRACKER_DB", DEFAULT_DATABASE_PATH)
