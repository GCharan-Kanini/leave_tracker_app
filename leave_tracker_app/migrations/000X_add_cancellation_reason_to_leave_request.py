"""Schema migration for adding cancellation_reason to leave_request records.

This repository currently uses an in-memory model for the cancellation UI flow;
this migration documents the intended schema addition for database-backed variants.
"""

from __future__ import annotations


def upgrade() -> str:
    """Return the forward migration SQL statement.

    Returns:
        SQL used to add a nullable cancellation_reason column.
    """
    return "ALTER TABLE leave_requests ADD COLUMN cancellation_reason TEXT NULL;"


def downgrade() -> str:
    """Return the rollback migration SQL statement.

    Returns:
        SQL describing the rollback intent.
    """
    return "-- rollback requires table rebuild in SQLite; omitted in in-memory mode"
