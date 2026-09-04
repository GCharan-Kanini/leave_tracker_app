"""Domain models and exceptions for the leave-tracking service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class LeaveType(Enum):
    """Represents the supported types of leave."""

    CASUAL = "CASUAL"
    SICK = "SICK"
    VACATION = "VACATION"


class LeaveStatus(Enum):
    """Represents lifecycle states for a leave request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveTrackerError(Exception):
    """Base class for all domain-specific leave tracker errors."""


class DuplicateEmployeeError(LeaveTrackerError):
    """Raised when attempting to register an employee ID that already exists."""


class UnknownEmployeeError(LeaveTrackerError):
    """Raised when an operation references a non-existent employee ID."""


class InsufficientBalanceError(LeaveTrackerError):
    """Raised when a leave request exceeds available leave balance."""


class NotAuthorizedError(LeaveTrackerError):
    """Raised when an actor attempts a workflow operation without permission."""


class InvalidStateError(LeaveTrackerError):
    """Raised when a workflow operation is invalid for the request's current state."""


@dataclass(slots=True)
class Employee:
    """Represents an employee in the organization.

    Args:
        employee_id: Unique identifier of the employee.
        name: Human-readable employee name.
        email: Employee email address.
        manager_id: Employee ID of the direct manager, if any.
    """

    employee_id: str
    name: str
    email: str
    manager_id: str | None = None


@dataclass(slots=True)
class LeaveRequest:
    """Represents a leave request made by an employee.

    Args:
        request_id: Unique leave request identifier.
        employee_id: Employee ID who created the request.
        leave_type: Leave category applied for.
        start_date: First day of leave (inclusive).
        end_date: Last day of leave (inclusive).
        reason: Employee's reason for the leave request.
        requested_days: Number of requested leave days.
        status: Current request status in the workflow.
    """

    request_id: str
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    requested_days: int
    status: str = field(default=LeaveStatus.PENDING.value)
