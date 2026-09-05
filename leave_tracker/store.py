"""In-memory persistence store for leave requests and employees."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from leave_tracker.models import Employee, LeaveRequest, LeaveStatus, LeaveType


@dataclass(slots=True)
class InMemoryLeaveStore:
    """Holds employee and leave-request state for API and tests.

    The store intentionally keeps all data in memory and exposes simple CRUD-like
    methods used by tests and API handlers.
    """

    _employees: dict[str, Employee]
    _requests_by_id: dict[str, LeaveRequest]
    _request_order: list[str]
    _next_request_number: int

    def __init__(self) -> None:
        """Initialize an empty store."""
        self._employees = {}
        self._requests_by_id = {}
        self._request_order = []
        self._next_request_number = 1

    def clear(self) -> None:
        """Reset all in-memory state."""
        self._employees.clear()
        self._requests_by_id.clear()
        self._request_order.clear()
        self._next_request_number = 1

    def add_employee(
        self,
        employee_id: str,
        name: str,
        email: str,
        manager_id: str | None = None,
    ) -> Employee:
        """Create and store an employee.

        Args:
            employee_id: Unique employee identifier.
            name: Employee display name.
            email: Employee email address.
            manager_id: Optional manager identifier.

        Returns:
            The created employee model.

        Raises:
            ValueError: If the employee already exists.
        """
        if employee_id in self._employees:
            raise ValueError(f"employee {employee_id!r} already exists")

        employee = Employee(
            employee_id=employee_id,
            name=name,
            email=email,
            manager_id=manager_id,
        )
        self._employees[employee_id] = employee
        return employee

    def has_employee(self, employee_id: str) -> bool:
        """Return whether an employee exists."""
        return employee_id in self._employees

    def add_leave_request(
        self,
        request_id: str,
        employee_id: str,
        leave_type: LeaveType | str,
        start_date: date | str,
        end_date: date | str,
        reason: str,
        requested_days: int,
    ) -> LeaveRequest:
        """Create and store a leave request.

        Args:
            request_id: Request identifier.
            employee_id: Request owner.
            leave_type: Leave type enum or value.
            start_date: Inclusive start date.
            end_date: Inclusive end date.
            reason: Employee reason text.
            requested_days: Requested day count.

        Returns:
            The stored leave request.

        Raises:
            ValueError: If request or employee is invalid.
        """
        if request_id in self._requests_by_id:
            raise ValueError(f"request {request_id!r} already exists")
        if employee_id not in self._employees:
            raise ValueError(f"employee {employee_id!r} not found")

        parsed_leave_type = self._coerce_leave_type(leave_type)
        parsed_start = self._coerce_date(start_date)
        parsed_end = self._coerce_date(end_date)

        request = LeaveRequest(
            request_id=request_id,
            employee_id=employee_id,
            leave_type=parsed_leave_type,
            start_date=parsed_start,
            end_date=parsed_end,
            reason=reason,
            requested_days=requested_days,
            status=LeaveStatus.PENDING.value,
        )
        self._requests_by_id[request_id] = request
        self._request_order.append(request_id)
        return request

    def create_leave_request(
        self,
        employee_id: str,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        reason: str,
        requested_days: int,
    ) -> LeaveRequest:
        """Create a new leave request with an auto-generated identifier."""
        request_id = f"req{self._next_request_number}"
        self._next_request_number += 1
        return self.add_leave_request(
            request_id=request_id,
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            requested_days=requested_days,
        )

    def update_request_status(self, request_id: str, status: LeaveStatus | str) -> None:
        """Update a request status in place.

        Args:
            request_id: Target request identifier.
            status: New status enum or value.

        Raises:
            ValueError: If request_id is unknown.
        """
        request = self.get_request(request_id)
        request.status = self._coerce_status(status)

    def get_request(self, request_id: str) -> LeaveRequest:
        """Fetch a request by id.

        Raises:
            ValueError: If request_id does not exist.
        """
        request = self._requests_by_id.get(request_id)
        if request is None:
            raise ValueError(f"request {request_id!r} not found")
        return request

    def get_employee_requests(self, employee_id: str) -> list[LeaveRequest]:
        """Return all requests for an employee in insertion order."""
        return [
            self._requests_by_id[request_id]
            for request_id in self._request_order
            if self._requests_by_id[request_id].employee_id == employee_id
        ]

    @staticmethod
    def _coerce_leave_type(leave_type: LeaveType | str) -> LeaveType:
        """Convert leave type input into a `LeaveType` enum."""
        if isinstance(leave_type, LeaveType):
            return leave_type
        return LeaveType[leave_type.upper()]

    @staticmethod
    def _coerce_status(status: LeaveStatus | str) -> str:
        """Convert status input into serialized status value."""
        if isinstance(status, LeaveStatus):
            return status.value
        normalized = status.upper()
        return LeaveStatus[normalized].value

    @staticmethod
    def _coerce_date(value: date | str) -> date:
        """Convert a date input to a `date` instance."""
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)


store = InMemoryLeaveStore()
"""Global in-memory store used by API handlers and tests."""
