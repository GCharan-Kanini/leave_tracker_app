"""Domain model for employee leave requests in the cancellation UI flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(slots=True)
class LeaveRequest:
    """Represents a leave request tracked by the employee-facing cancellation flow.

    Args:
        id: Unique leave request identifier.
        employee_id: Employee who owns the request.
        start_date: Inclusive start date string shown in the UI.
        end_date: Inclusive end date string shown in the UI.
        status: Current request status value.
        notes: Optional free-text notes attached to the request.
        cancellation_reason: Optional employee-provided reason captured at cancellation.
    """

    id: int
    employee_id: int
    start_date: str
    end_date: str
    status: str
    notes: str | None = None
    cancellation_reason: str | None = None

    _records: ClassVar[dict[int, "LeaveRequest"]] = {}

    def __post_init__(self) -> None:
        """Persist this request in the in-memory backing store."""
        LeaveRequest._records[self.id] = self

    @classmethod
    def get(cls, request_id: int) -> "LeaveRequest":
        """Fetch a request by identifier.

        Args:
            request_id: Leave request identifier.

        Returns:
            The matching leave request.

        Raises:
            KeyError: If no request exists for request_id.
        """
        if request_id not in cls._records:
            raise KeyError(f"leave request {request_id} not found")
        return cls._records[request_id]

    @classmethod
    def get_by_employee(cls, employee_id: int) -> list["LeaveRequest"]:
        """Return all requests for an employee.

        Args:
            employee_id: Employee identifier.

        Returns:
            Requests owned by the employee, preserving insertion order.
        """
        return [request for request in cls._records.values() if request.employee_id == employee_id]

    @classmethod
    def list_all(cls) -> list["LeaveRequest"]:
        """Return all tracked leave requests."""
        return list(cls._records.values())
