"""FastAPI entrypoint for the Leave Tracker application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from app.db import get_connection, initialize_database
from app.models import (
    BalanceResponse,
    EmployeeCreate,
    EmployeeResponse,
    LeaveApplyRequest,
    LeaveApplyResponse,
    LeaveHistoryEntry,
    LeaveTypeEntry,
    LeaveTypeUpdateRequest,
    ManagerActionRequest,
    ManagerPendingEntry,
    SummaryEntry,
    TeamCalendarEntry,
)
from app.services import _actor_can_manage, _employee_or_404, calculate_working_days, get_balance_for_employee, month_bounds


app = FastAPI(title="Leave Tracker")


@app.on_event("startup")
def startup() -> None:
    """Initialize the active SQLite database on app startup."""
    initialize_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health probe endpoint."""
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    """Serve the browser UI page."""
    return FileResponse(Path("static/index.html"))


@app.get("/static/{asset_path:path}")
def static_asset(asset_path: str) -> FileResponse:
    """Serve static frontend assets."""
    file_path = Path("static") / asset_path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"asset {asset_path} not found")
    return FileResponse(file_path)


@app.post("/api/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(payload: EmployeeCreate) -> Any:
    """Create an employee when email is unique."""
    with get_connection() as connection:
        existing = connection.execute("SELECT id FROM employees WHERE email = ?", (payload.email,)).fetchone()
        if existing is not None:
            raise HTTPException(status_code=409, detail=f"email {payload.email} already exists")

        if payload.manager_id is not None:
            manager = connection.execute(
                "SELECT id FROM employees WHERE id = ?", (payload.manager_id,)
            ).fetchone()
            if manager is None:
                raise HTTPException(status_code=404, detail=f"manager {payload.manager_id} not found")

        cursor = connection.execute(
            """
            INSERT INTO employees(name, email, role, manager_id)
            VALUES (?, ?, ?, ?)
            """,
            (payload.name, payload.email, payload.role.value, payload.manager_id),
        )
        employee_id = int(cursor.lastrowid)
        row = connection.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    return dict(row)


@app.get("/api/employees/{employee_id}/balance", response_model=BalanceResponse)
def employee_balance(employee_id: int) -> dict[str, int]:
    """Return remaining leave balance for an employee."""
    return get_balance_for_employee(employee_id)


@app.post("/api/leaves/apply", response_model=LeaveApplyResponse, status_code=201)
def apply_leave(payload: LeaveApplyRequest) -> Any:
    """Apply for leave after validating employee and available balance."""
    _employee_or_404(payload.employee_id)
    calculated_days = calculate_working_days(payload.start_date, payload.end_date)
    working_days = max(1, calculated_days)

    balance = get_balance_for_employee(payload.employee_id)
    leave_name = payload.leave_type.value
    remaining = balance.get(leave_name, 0)
    if working_days > remaining:
        raise HTTPException(
            status_code=422,
            detail=(
                f"requested {working_days} days exceeds remaining balance {remaining} "
                f"for leave type {leave_name}"
            ),
        )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leave_requests(employee_id, leave_type, start_date, end_date, reason, status, working_days)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                payload.employee_id,
                leave_name,
                payload.start_date.isoformat(),
                payload.end_date.isoformat(),
                payload.reason,
                working_days,
            ),
        )
        request_id = int(cursor.lastrowid)
        row = connection.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()

    return {
        "request_id": row["id"],
        "employee_id": row["employee_id"],
        "leave_type": row["leave_type"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "reason": row["reason"],
        "status": row["status"],
        "working_days": row["working_days"],
    }


@app.get("/api/leaves/myrequests", response_model=list[LeaveHistoryEntry])
def my_requests(employee_id: int = Query(...)) -> list[dict[str, Any]]:
    """List leave requests for an employee from newest to oldest."""
    _employee_or_404(employee_id)
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, employee_id, leave_type, start_date, end_date, reason, status, working_days, created_at
            FROM leave_requests
            WHERE employee_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (employee_id,),
        ).fetchall()
    return [
        {
            "request_id": row["id"],
            "employee_id": row["employee_id"],
            "leave_type": row["leave_type"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "reason": row["reason"],
            "status": row["status"],
            "working_days": row["working_days"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def _act_on_request(request_id: int, manager_id: int, target_status: str) -> dict[str, Any]:
    """Approve or reject a pending leave request with authorization checks."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"leave request {request_id} not found")
        request = dict(row)
        if request["status"] != "pending":
            raise HTTPException(status_code=409, detail=f"request {request_id} is not pending")

        employee = connection.execute(
            "SELECT * FROM employees WHERE id = ?", (request["employee_id"],)
        ).fetchone()
        if employee is None:
            raise HTTPException(status_code=404, detail=f"employee {request['employee_id']} not found")

    if not _actor_can_manage(manager_id, dict(employee)):
        raise HTTPException(
            status_code=403,
            detail=f"manager {manager_id} is not allowed to act on request {request_id}",
        )

    with get_connection() as connection:
        connection.execute(
            "UPDATE leave_requests SET status = ?, reviewed_by = ? WHERE id = ?",
            (target_status, manager_id, request_id),
        )
        updated = connection.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()

    return {
        "request_id": updated["id"],
        "employee_id": updated["employee_id"],
        "leave_type": updated["leave_type"],
        "start_date": updated["start_date"],
        "end_date": updated["end_date"],
        "reason": updated["reason"],
        "status": updated["status"],
        "working_days": updated["working_days"],
    }


@app.put("/api/leaves/{request_id}/approve")
def approve_leave(request_id: int, payload: ManagerActionRequest) -> dict[str, Any]:
    """Approve a pending leave request when actor is manager or admin."""
    return _act_on_request(request_id, payload.manager_id, "approved")


@app.put("/api/leaves/{request_id}/reject")
def reject_leave(request_id: int, payload: ManagerActionRequest) -> dict[str, Any]:
    """Reject a pending leave request when actor is manager or admin."""
    return _act_on_request(request_id, payload.manager_id, "rejected")


@app.delete("/api/leaves/{request_id}")
def cancel_leave(request_id: int, employee_id: int = Query(...)) -> dict[str, str]:
    """Cancel the employee's own pending leave request."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"leave request {request_id} not found")
        request = dict(row)
        if request["employee_id"] != employee_id:
            raise HTTPException(
                status_code=403,
                detail=f"employee {employee_id} cannot cancel request owned by {request['employee_id']}",
            )
        if request["status"] != "pending":
            raise HTTPException(status_code=409, detail=f"request {request_id} is not pending")

        connection.execute("UPDATE leave_requests SET status = 'cancelled' WHERE id = ?", (request_id,))
    return {"status": "cancelled"}


@app.get("/api/managers/{manager_id}/pending", response_model=list[ManagerPendingEntry])
def manager_pending(manager_id: int) -> list[dict[str, Any]]:
    """Return pending requests from the manager's direct reports."""
    with get_connection() as connection:
        manager = connection.execute("SELECT * FROM employees WHERE id = ?", (manager_id,)).fetchone()
        if manager is None:
            raise HTTPException(status_code=404, detail=f"manager {manager_id} not found")

        rows = connection.execute(
            """
            SELECT lr.id, lr.employee_id, e.name AS employee_name, lr.leave_type, lr.start_date,
                   lr.end_date, lr.reason, lr.status, lr.working_days, lr.created_at
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            WHERE e.manager_id = ? AND lr.status = 'pending'
            ORDER BY datetime(lr.created_at) DESC, lr.id DESC
            """,
            (manager_id,),
        ).fetchall()
    return [
        {
            "request_id": row["id"],
            "employee_id": row["employee_id"],
            "employee_name": row["employee_name"],
            "leave_type": row["leave_type"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "reason": row["reason"],
            "status": row["status"],
            "working_days": row["working_days"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@app.get("/api/managers/{manager_id}/calendar", response_model=list[TeamCalendarEntry])
def manager_calendar(manager_id: int, month: str = Query(...)) -> list[dict[str, Any]]:
    """Return approved team leave entries overlapping the provided month."""
    start, end = month_bounds(month)
    with get_connection() as connection:
        manager = connection.execute("SELECT * FROM employees WHERE id = ?", (manager_id,)).fetchone()
        if manager is None:
            raise HTTPException(status_code=404, detail=f"manager {manager_id} not found")

        rows = connection.execute(
            """
            SELECT lr.employee_id, e.name, lr.start_date, lr.end_date, lr.leave_type
            FROM leave_requests lr
            JOIN employees e ON e.id = lr.employee_id
            WHERE e.manager_id = ?
              AND lr.status = 'approved'
              AND date(lr.start_date) <= date(?)
              AND date(lr.end_date) >= date(?)
            ORDER BY date(lr.start_date) ASC, lr.id ASC
            """,
            (manager_id, end.isoformat(), start.isoformat()),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/leave-types", response_model=list[LeaveTypeEntry])
def list_leave_types() -> list[dict[str, Any]]:
    """List configured leave types with yearly allowances."""
    with get_connection() as connection:
        rows = connection.execute("SELECT type, allowance FROM leave_types ORDER BY type ASC").fetchall()
    return [dict(row) for row in rows]


@app.put("/api/leave-types/{leave_type}")
def update_leave_type(leave_type: str, payload: LeaveTypeUpdateRequest) -> dict[str, Any]:
    """Update a leave type allowance when the actor is an admin."""
    with get_connection() as connection:
        admin = connection.execute("SELECT * FROM employees WHERE id = ?", (payload.admin_id,)).fetchone()
        if admin is None:
            raise HTTPException(status_code=404, detail=f"admin {payload.admin_id} not found")
        if admin["role"] != "admin":
            raise HTTPException(status_code=403, detail=f"employee {payload.admin_id} is not admin")

        existing = connection.execute("SELECT type FROM leave_types WHERE type = ?", (leave_type,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"leave type {leave_type} not found")

        connection.execute(
            "UPDATE leave_types SET allowance = ? WHERE type = ?",
            (payload.allowance, leave_type),
        )
    return {"type": leave_type, "allowance": payload.allowance}


@app.get("/api/reports/summary", response_model=list[SummaryEntry])
def summary_report(admin_id: int = Query(...)) -> list[dict[str, Any]]:
    """Return per-employee approved totals by leave type for admins."""
    with get_connection() as connection:
        admin = connection.execute("SELECT * FROM employees WHERE id = ?", (admin_id,)).fetchone()
        if admin is None:
            raise HTTPException(status_code=404, detail=f"admin {admin_id} not found")
        if admin["role"] != "admin":
            raise HTTPException(status_code=403, detail=f"employee {admin_id} is not admin")

        rows = connection.execute(
            """
            SELECT
                e.id AS employee_id,
                e.name,
                COALESCE(SUM(CASE WHEN lr.leave_type = 'casual' AND lr.status = 'approved' THEN lr.working_days ELSE 0 END), 0) AS casual,
                COALESCE(SUM(CASE WHEN lr.leave_type = 'sick' AND lr.status = 'approved' THEN lr.working_days ELSE 0 END), 0) AS sick,
                COALESCE(SUM(CASE WHEN lr.leave_type = 'vacation' AND lr.status = 'approved' THEN lr.working_days ELSE 0 END), 0) AS vacation
            FROM employees e
            LEFT JOIN leave_requests lr ON lr.employee_id = e.id
            GROUP BY e.id, e.name
            ORDER BY e.id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]
