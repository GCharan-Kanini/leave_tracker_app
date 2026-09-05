"""Tests for leave balance API endpoints and calculations."""

import pytest
from fastapi.testclient import TestClient
from app import app
from leave_tracker.models import LeaveStatus, LeaveType
from leave_tracker.store import store

client = TestClient(app)


def test_api_returns_complete_balance_structure():
    """Test AC-1: API returns employee leave balance with fixed annual allowance, consumed, pending, and remaining days."""
    # Setup employee
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Get balance
    response = client.get("/api/employees/emp1/balance")
    
    assert response.status_code == 200
    balance = response.json()
    
    # Verify structure includes all required fields
    assert "annual_allowance" in balance
    assert "consumed_days" in balance
    assert "pending_days" in balance
    assert "remaining_days" in balance
    
    # Verify fixed annual allowance
    assert balance["annual_allowance"] == 24
    
    # Verify initial state for new employee
    assert balance["consumed_days"] == 0
    assert balance["pending_days"] == 0
    assert balance["remaining_days"] == 24


def test_approved_vs_pending_separation():
    """Test AC-2: Only approved requests count as consumed; pending requests are reported separately."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Add approved request
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-05", "Holiday", 5)
    store.update_request_status("req1", LeaveStatus.APPROVED)
    
    # Add pending request
    store.add_leave_request("req2", "emp1", LeaveType.VACATION, "2024-02-01", "2024-02-03", "Break", 3)
    
    response = client.get("/api/employees/emp1/balance")
    balance = response.json()
    
    # Approved request counts as consumed
    assert balance["consumed_days"] == 5
    
    # Pending request reported separately, not in consumed
    assert balance["pending_days"] == 3
    
    # Remaining = 24 - 5 (approved) = 19
    assert balance["remaining_days"] == 19


def test_rejected_cancelled_excluded_from_consumed():
    """Test AC-3: Rejected and cancelled requests are excluded from consumed leave calculations."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Add approved request (should count)
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-02", "Holiday", 2)
    store.update_request_status("req1", LeaveStatus.APPROVED)
    
    # Add rejected request (should not count)
    store.add_leave_request("req2", "emp1", LeaveType.VACATION, "2024-02-01", "2024-02-03", "Break", 3)
    store.update_request_status("req2", LeaveStatus.REJECTED)
    
    # Add cancelled request (should not count)
    store.add_leave_request("req3", "emp1", LeaveType.VACATION, "2024-03-01", "2024-03-04", "Trip", 4)
    store.update_request_status("req3", LeaveStatus.CANCELLED)
    
    response = client.get("/api/employees/emp1/balance")
    balance = response.json()
    
    # Only approved request counts as consumed
    assert balance["consumed_days"] == 2
    assert balance["pending_days"] == 0
    assert balance["remaining_days"] == 22


def test_overdraw_submission_refused_not_stored():
    """Test AC-4: Submitting request exceeding remaining days is refused with clear reason and not stored."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Use up most of the allowance
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-20", "Holiday", 20)
    store.update_request_status("req1", LeaveStatus.APPROVED)
    
    # Get initial request count
    initial_requests = len(store.get_employee_requests("emp1"))
    
    # Try to submit request exceeding remaining balance (4 remaining, requesting 10)
    response = client.post("/api/leaves/apply", json={
        "employee_id": "emp1",
        "leave_type": "VACATION",
        "start_date": "2024-02-01",
        "end_date": "2024-02-10",
        "reason": "Long trip"
    })
    
    # Request should be refused
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    
    # Error should mention remaining days
    assert "remaining" in error_detail.lower()
    assert "4" in error_detail  # Remaining days count
    
    # Request should not be stored
    final_requests = len(store.get_employee_requests("emp1"))
    assert final_requests == initial_requests
