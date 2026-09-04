"""Service helpers encapsulating Leave Tracker business rules."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException

from app.db import get_connection
from app.models import LeaveType, Role


def calculate_working_days(start_date: date, end_date: date) -> int:
    """Count inclusive working days between two dates, excluding weekends."""
    days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def _employee_or_404(employee_id: int) -> dict[str, Any]:
    """Fetch employee row as dict or raise 404."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"employee {employee_id} not found")
        return dict(row)


def _actor_can_manage(actor_id: int, employee_row: dict[str, Any]) -> bool:
    """Return whether actor is admin or direct manager of employee."""
    with get_connection() as connection:
        actor = connection.execute("SELECT * FROM employees WHERE id = ?", (actor_id,)).fetchone()
        if actor is None:
            return False
        actor_role = actor["role"]
        if actor_role == Role.ADMIN.value:
            return True
        return actor_role == Role.MANAGER.value and employee_row.get("manager_id") == actor["id"]


def get_balance_for_employee(employee_id: int) -> dict[str, int]:
    """Compute employee leave balance from allowances minus approved leave."""
    _employee_or_404(employee_id)
    with get_connection() as connection:
        leave_types = connection.execute("SELECT type, allowance FROM leave_types").fetchall()
        approved = connection.execute(
            """
            SELECT leave_type, COALESCE(SUM(working_days), 0) AS used_days
            FROM leave_requests
            WHERE employee_id = ? AND status = 'approved'
            GROUP BY leave_type
            """,
            (employee_id,),
        ).fetchall()

    allowances = {row["type"]: int(row["allowance"]) for row in leave_types}
    used = {row["leave_type"]: int(row["used_days"]) for row in approved}
    return {
        "casual": max(allowances.get("casual", 0) - used.get("casual", 0), 0),
        "sick": max(allowances.get("sick", 0) - used.get("sick", 0), 0),
        "vacation": max(allowances.get("vacation", 0) - used.get("vacation", 0), 0),
    }


def month_bounds(month: str) -> tuple[date, date]:
    """Parse YYYY-MM into first/last day bounds."""
    try:
        start = datetime.strptime(month, "%Y-%m").date().replace(day=1)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid month value: {month}") from exc
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    end = next_month - timedelta(days=1)
    return start, end
