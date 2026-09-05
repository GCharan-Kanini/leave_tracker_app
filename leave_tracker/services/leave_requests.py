"""Business rules for leave balances, submissions, and cancellations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from leave_tracker.models import (
    InsufficientBalanceError,
    InvalidStateError,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    UnknownEmployeeError,
)
from leave_tracker.store import InMemoryLeaveStore

ANNUAL_ALLOWANCE_DAYS = 24


@dataclass(slots=True)
class LeaveBalance:
    """Aggregated balance figures for an employee.

    Args:
        annual_allowance: Fixed yearly allowance in days.
        consumed_days: Days consumed by approved requests.
        pending_days: Days currently awaiting approval.
        remaining_days: Days still available to request.
    """

    annual_allowance: int
    consumed_days: int
    pending_days: int
    remaining_days: int

    def to_dict(self) -> dict[str, int]:
        """Return a JSON-serializable mapping of balance fields."""
        return {
            "annual_allowance": self.annual_allowance,
            "consumed_days": self.consumed_days,
            "pending_days": self.pending_days,
            "remaining_days": self.remaining_days,
        }


def calculate_inclusive_days(start_date: date, end_date: date) -> int:
    """Calculate inclusive whole-day span between dates.

    Args:
        start_date: First date in the request range.
        end_date: Last date in the request range.

    Returns:
        The number of days covered by the range inclusively.

    Raises:
        ValueError: If end_date is before start_date.
    """
    if end_date < start_date:
        raise ValueError(
            f"end_date {end_date.isoformat()} is before start_date {start_date.isoformat()}"
        )
    return (end_date - start_date).days + 1


def get_employee_balance(employee_id: str, store: InMemoryLeaveStore) -> LeaveBalance:
    """Compute balance totals for an employee.

    Args:
        employee_id: Employee identifier.
        store: In-memory backing store.

    Returns:
        Aggregated leave balance values.

    Raises:
        UnknownEmployeeError: If the employee does not exist.
    """
    if not store.has_employee(employee_id):
        raise UnknownEmployeeError(f"employee {employee_id!r} not found")

    consumed_days = 0
    pending_days = 0
    for request in store.get_employee_requests(employee_id):
        if request.status == LeaveStatus.APPROVED.value:
            consumed_days += request.requested_days
        elif request.status == LeaveStatus.PENDING.value:
            pending_days += request.requested_days

    remaining_days = max(ANNUAL_ALLOWANCE_DAYS - consumed_days, 0)
    return LeaveBalance(
        annual_allowance=ANNUAL_ALLOWANCE_DAYS,
        consumed_days=consumed_days,
        pending_days=pending_days,
        remaining_days=remaining_days,
    )


def submit_leave_request(
    employee_id: str,
    leave_type: LeaveType,
    start_date: date,
    end_date: date,
    reason: str,
    store: InMemoryLeaveStore,
) -> LeaveRequest:
    """Validate and create a pending leave request.

    Args:
        employee_id: Employee identifier.
        leave_type: Requested leave type.
        start_date: Inclusive start date.
        end_date: Inclusive end date.
        reason: Employee-provided reason.
        store: In-memory backing store.

    Returns:
        The created pending leave request.

    Raises:
        UnknownEmployeeError: If employee does not exist.
        InsufficientBalanceError: If request exceeds remaining balance.
        ValueError: If date range is invalid.
    """
    if not store.has_employee(employee_id):
        raise UnknownEmployeeError(f"employee {employee_id!r} not found")

    requested_days = calculate_inclusive_days(start_date, end_date)
    balance = get_employee_balance(employee_id, store)
    if requested_days > balance.remaining_days:
        raise InsufficientBalanceError(
            f"Cannot submit {requested_days} days; only {balance.remaining_days} remaining days available."
        )

    return store.create_leave_request(
        employee_id=employee_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        requested_days=requested_days,
    )


def cancel_leave_request(
    request_id: str,
    employee_id: str,
    store: InMemoryLeaveStore,
) -> LeaveRequest:
    """Cancel a pending request owned by the employee.

    Args:
        request_id: Leave request identifier.
        employee_id: Employee attempting cancellation.
        store: In-memory backing store.

    Returns:
        The updated leave request in cancelled state.

    Raises:
        ValueError: If request does not exist.
        UnknownEmployeeError: If employee does not exist.
        InvalidStateError: If request is not cancellable.
    """
    if not store.has_employee(employee_id):
        raise UnknownEmployeeError(f"employee {employee_id!r} not found")

    request = store.get_request(request_id)

    if request.employee_id != employee_id:
        raise InvalidStateError(
            f"Cannot cancel request {request_id!r}: employee {employee_id!r} does not own it."
        )

    if request.status != LeaveStatus.PENDING.value:
        raise InvalidStateError(
            f"Cannot cancel request {request_id!r}: it is already {request.status.lower()}."
        )

    store.update_request_status(request_id, LeaveStatus.CANCELLED)
    return store.get_request(request_id)


def list_employee_requests(employee_id: str, store: InMemoryLeaveStore) -> list[LeaveRequest]:
    """Return all requests for an employee.

    Args:
        employee_id: Employee identifier.
        store: In-memory backing store.

    Returns:
        Requests in creation order.

    Raises:
        UnknownEmployeeError: If employee does not exist.
    """
    if not store.has_employee(employee_id):
        raise UnknownEmployeeError(f"employee {employee_id!r} not found")
    return store.get_employee_requests(employee_id)


def serialize_request(request: LeaveRequest) -> dict[str, str | int]:
    """Serialize a leave request into API response shape."""
    return {
        "request_id": request.request_id,
        "employee_id": request.employee_id,
        "leave_type": request.leave_type.value,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "reason": request.reason,
        "status": request.status,
        "working_days": request.requested_days,
    }
