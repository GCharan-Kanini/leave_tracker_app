"""In-memory leave-tracking service with approval workflow support."""

from __future__ import annotations

from datetime import date

from .models import (
    DuplicateEmployeeError,
    Employee,
    InsufficientBalanceError,
    InvalidStateError,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    NotAuthorizedError,
    UnknownEmployeeError,
)


class LeaveTracker:
    """Coordinates employees, leave balances, and request workflows in memory."""

    def __init__(self) -> None:
        """Initialize an empty leave-tracking state."""
        self._employees: dict[str, Employee] = {}
        self._balances: dict[str, dict[LeaveType, int]] = {}
        self._requests_by_id: dict[str, LeaveRequest] = {}
        self._requests_in_order: list[LeaveRequest] = []
        self._next_request_number: int = 1

    def add_employee(
        self,
        employee_id: str,
        name: str,
        email: str,
        manager_id: str | None = None,
    ) -> None:
        """Register a new employee.

        Args:
            employee_id: Unique identifier for the employee.
            name: Employee name.
            email: Employee email address.
            manager_id: Optional direct manager employee ID.

        Raises:
            DuplicateEmployeeError: If employee_id is already registered.
        """
        if employee_id in self._employees:
            raise DuplicateEmployeeError(
                f"Employee with id {employee_id!r} is already registered"
            )

        self._employees[employee_id] = Employee(
            employee_id=employee_id,
            name=name,
            email=email,
            manager_id=manager_id,
        )
        self._balances[employee_id] = {}

    def set_balance(self, employee_id: str, leave_type: LeaveType, days: int) -> None:
        """Set available leave balance for an employee and leave type.

        Args:
            employee_id: Employee whose balance will be stored.
            leave_type: Leave category to update.
            days: Balance in days.

        Raises:
            UnknownEmployeeError: If employee_id is not registered.
            ValueError: If days is negative.
        """
        self._ensure_employee_exists(employee_id)

        if days < 0:
            raise ValueError(f"Balance days cannot be negative: {days}")

        self._balances[employee_id][leave_type] = days

    def get_balance(self, employee_id: str, leave_type: LeaveType) -> int:
        """Return the available leave balance for an employee and leave type.

        Args:
            employee_id: Employee whose balance is requested.
            leave_type: Leave category to read.

        Returns:
            The currently available balance in days.

        Raises:
            UnknownEmployeeError: If employee_id is not registered.
        """
        self._ensure_employee_exists(employee_id)
        return self._balances[employee_id].get(leave_type, 0)

    def apply(
        self,
        employee_id: str,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        reason: str,
    ) -> LeaveRequest:
        """Create a pending leave request for an employee.

        Args:
            employee_id: Employee requesting leave.
            leave_type: Requested leave category.
            start_date: First day of leave (inclusive).
            end_date: Last day of leave (inclusive).
            reason: Reason for leave.

        Returns:
            The newly created leave request in pending state.

        Raises:
            UnknownEmployeeError: If employee_id is not registered.
            ValueError: If end_date is before start_date.
            InsufficientBalanceError: If requested days exceed current balance.
        """
        self._ensure_employee_exists(employee_id)

        if end_date < start_date:
            raise ValueError(
                f"end_date {end_date.isoformat()} cannot be before start_date {start_date.isoformat()}"
            )

        requested_days = self._calculate_requested_days(start_date, end_date)
        available_days = self.get_balance(employee_id, leave_type)
        if requested_days > available_days:
            raise InsufficientBalanceError(
                "Insufficient balance for "
                f"employee {employee_id!r}, leave type {leave_type.value!r}: "
                f"requested {requested_days}, available {available_days}"
            )

        request_id = f"LR-{self._next_request_number}"
        self._next_request_number += 1

        request = LeaveRequest(
            request_id=request_id,
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            requested_days=requested_days,
            status=LeaveStatus.PENDING.value,
        )
        self._requests_by_id[request_id] = request
        self._requests_in_order.append(request)
        return request

    def approve(self, request_id: str, manager_id: str) -> None:
        """Approve a pending leave request and deduct balance.

        Args:
            request_id: Leave request identifier.
            manager_id: Employee ID attempting approval.

        Raises:
            ValueError: If request_id does not exist.
            NotAuthorizedError: If manager_id is not the request owner's manager.
            InvalidStateError: If request is not in PENDING state.
        """
        request = self._get_request(request_id)
        employee = self._employees[request.employee_id]

        if employee.manager_id != manager_id:
            raise NotAuthorizedError(
                f"Manager {manager_id!r} is not authorized to approve request {request_id!r}"
            )

        if request.status != LeaveStatus.PENDING.value:
            raise InvalidStateError(
                f"Request {request_id!r} is in state {request.status!r}, expected PENDING"
            )

        current_balance = self.get_balance(request.employee_id, request.leave_type)
        self._balances[request.employee_id][request.leave_type] = (
            current_balance - request.requested_days
        )
        request.status = LeaveStatus.APPROVED.value

    def reject(self, request_id: str, manager_id: str) -> None:
        """Reject a pending leave request without changing leave balance.

        Args:
            request_id: Leave request identifier.
            manager_id: Employee ID attempting rejection.

        Raises:
            ValueError: If request_id does not exist.
            NotAuthorizedError: If manager_id is not the request owner's manager.
            InvalidStateError: If request is not in PENDING state.
        """
        request = self._get_request(request_id)
        employee = self._employees[request.employee_id]

        if employee.manager_id != manager_id:
            raise NotAuthorizedError(
                f"Manager {manager_id!r} is not authorized to reject request {request_id!r}"
            )

        if request.status != LeaveStatus.PENDING.value:
            raise InvalidStateError(
                f"Request {request_id!r} is in state {request.status!r}, expected PENDING"
            )

        request.status = LeaveStatus.REJECTED.value

    def cancel(self, request_id: str, employee_id: str) -> None:
        """Cancel a pending request owned by the specified employee.

        Args:
            request_id: Leave request identifier.
            employee_id: Employee requesting cancellation.

        Raises:
            ValueError: If request_id does not exist.
            InvalidStateError: If request is not pending or not owned by employee_id.
        """
        request = self._get_request(request_id)

        if request.employee_id != employee_id:
            raise InvalidStateError(
                f"Employee {employee_id!r} cannot cancel request {request_id!r}"
            )

        if request.status != LeaveStatus.PENDING.value:
            raise InvalidStateError(
                f"Request {request_id!r} is in state {request.status!r}, expected PENDING"
            )

        request.status = LeaveStatus.CANCELLED.value

    def requests_for(self, employee_id: str) -> list[LeaveRequest]:
        """Return all requests created by an employee in creation order.

        Args:
            employee_id: Employee whose requests should be listed.

        Returns:
            A new list of leave requests belonging to employee_id.

        Raises:
            UnknownEmployeeError: If employee_id is not registered.
        """
        self._ensure_employee_exists(employee_id)
        return [
            request
            for request in self._requests_in_order
            if request.employee_id == employee_id
        ]

    def pending_for_manager(self, manager_id: str) -> list[LeaveRequest]:
        """Return pending requests for direct reports of the manager.

        Args:
            manager_id: Manager whose team requests should be listed.

        Returns:
            A new list of pending leave requests for direct reports.
        """
        return [
            request
            for request in self._requests_in_order
            if request.status == LeaveStatus.PENDING.value
            and self._employees[request.employee_id].manager_id == manager_id
        ]

    def _ensure_employee_exists(self, employee_id: str) -> None:
        """Validate that an employee ID exists in tracker state.

        Args:
            employee_id: Employee identifier to validate.

        Raises:
            UnknownEmployeeError: If employee_id does not exist.
        """
        if employee_id not in self._employees:
            raise UnknownEmployeeError(f"Employee with id {employee_id!r} is not registered")

    def _get_request(self, request_id: str) -> LeaveRequest:
        """Retrieve a leave request by ID.

        Args:
            request_id: Request identifier.

        Returns:
            The leave request instance.

        Raises:
            ValueError: If request_id does not exist.
        """
        request = self._requests_by_id.get(request_id)
        if request is None:
            raise ValueError(f"Unknown request id: {request_id!r}")
        return request

    @staticmethod
    def _calculate_requested_days(start_date: date, end_date: date) -> int:
        """Calculate inclusive number of leave days between two dates.

        Args:
            start_date: First day of leave (inclusive).
            end_date: Last day of leave (inclusive).

        Returns:
            Number of inclusive days in the requested period.
        """
        return (end_date - start_date).days + 1
