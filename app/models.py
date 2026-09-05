"""Pydantic and domain models for the Leave Tracker application."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Role(str, Enum):
    """Supported employee roles."""

    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class LeaveType(str, Enum):
    """Supported leave types."""

    CASUAL = "casual"
    SICK = "sick"
    VACATION = "vacation"


class EmployeeCreate(BaseModel):
    """Request body for creating an employee."""

    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    role: Role
    manager_id: Optional[int] = None


class EmployeeResponse(BaseModel):
    """Employee response payload."""

    id: int
    name: str
    email: str
    role: Role
    manager_id: Optional[int] = None


class LeaveApplyRequest(BaseModel):
    """Request body for applying leave."""

    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dates(self) -> "LeaveApplyRequest":
        """Ensure the end date is not before the start date."""
        if self.end_date < self.start_date:
            raise ValueError(
                f"end_date {self.end_date.isoformat()} is before start_date {self.start_date.isoformat()}"
            )
        return self


class LeaveApplyResponse(BaseModel):
    """Response payload for leave application."""

    request_id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: str
    working_days: int


class LeaveHistoryEntry(BaseModel):
    """Employee leave request history entry."""

    request_id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: str
    working_days: int
    cancellation_reason: Optional[str] = None
    created_at: str


class LeaveCancelRequest(BaseModel):
    """Request body for canceling a leave request."""

    cancellation_reason: str = Field(min_length=1)


class ManagerActionRequest(BaseModel):
    """Request body for manager approval or rejection actions."""

    manager_id: int


class ManagerPendingEntry(BaseModel):
    """Pending leave request entry for managers."""

    request_id: int
    employee_id: int
    employee_name: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: str
    working_days: int
    created_at: str


class TeamCalendarEntry(BaseModel):
    """Approved leave entry for manager calendar view."""

    employee_id: int
    name: str
    start_date: date
    end_date: date
    leave_type: LeaveType


class LeaveTypeEntry(BaseModel):
    """Leave type with configured yearly allowance."""

    type: LeaveType
    allowance: int = Field(ge=0)


class LeaveTypeUpdateRequest(BaseModel):
    """Request body for updating a leave type allowance."""

    allowance: int = Field(ge=0)
    admin_id: int


class SummaryEntry(BaseModel):
    """Summary of approved leave totals per employee."""

    employee_id: int
    name: str
    casual: int
    sick: int
    vacation: int


class BalanceResponse(BaseModel):
    """Remaining leave balance for each leave type."""

    casual: int
    sick: int
    vacation: int
