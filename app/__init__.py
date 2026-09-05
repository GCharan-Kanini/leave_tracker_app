"""Compatibility FastAPI app surface for in-memory leave tracker tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator, model_validator

from leave_tracker.models import (
    InsufficientBalanceError,
    InvalidStateError,
    LeaveType,
    UnknownEmployeeError,
)
from leave_tracker.services.leave_requests import (
    cancel_leave_request,
    get_employee_balance,
    list_employee_requests,
    serialize_request,
    submit_leave_request,
)
from leave_tracker.store import store


class LeaveApplyPayload(BaseModel):
    """Request body for creating a leave request.

    Args:
        employee_id: Identifier of the employee applying for leave.
        leave_type: Leave category requested.
        start_date: Inclusive start date.
        end_date: Inclusive end date.
        reason: Free-text reason for leave.
    """

    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str) -> str:
        """Reject blank reasons after stripping whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("reason must not be blank")
        return stripped

    @model_validator(mode="after")
    def _validate_dates(self) -> "LeaveApplyPayload":
        """Ensure date range is valid and inclusive."""
        if self.end_date < self.start_date:
            raise ValueError(
                f"end_date {self.end_date.isoformat()} is before start_date {self.start_date.isoformat()}"
            )
        return self


app = FastAPI(title="Leave Tracker")


@app.get("/")
def index() -> FileResponse:
    """Serve the static single-page application."""
    return FileResponse(Path("static/index.html"))


@app.get("/api/employees/{employee_id}/balance")
def employee_balance(employee_id: str) -> dict[str, int]:
    """Return annual allowance, consumed, pending, and remaining leave totals."""
    try:
        return get_employee_balance(employee_id, store).to_dict()
    except UnknownEmployeeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/leaves/apply", status_code=201)
def apply_leave(payload: LeaveApplyPayload) -> dict[str, str | int]:
    """Submit a leave request after balance validation."""
    try:
        request = submit_leave_request(
            employee_id=payload.employee_id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            reason=payload.reason,
            store=store,
        )
        return serialize_request(request)
    except UnknownEmployeeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/leaves/myrequests")
def my_requests(employee_id: str = Query(...)) -> list[dict[str, Any]]:
    """Return the request history for the given employee."""
    try:
        requests = list_employee_requests(employee_id, store)
    except UnknownEmployeeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [serialize_request(request) for request in requests]


@app.delete("/api/leaves/{request_id}", status_code=204)
def cancel_request(request_id: str, employee_id: str = Query(...)) -> None:
    """Cancel a pending leave request owned by employee_id."""
    try:
        cancel_leave_request(request_id=request_id, employee_id=employee_id, store=store)
    except UnknownEmployeeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


__all__ = ["app"]

