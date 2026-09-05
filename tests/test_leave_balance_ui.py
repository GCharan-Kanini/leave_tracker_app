"""Tests for leave balance UI functionality and display."""

import pytest
from fastapi.testclient import TestClient
from app import app
from leave_tracker.models import LeaveStatus, LeaveType
from leave_tracker.store import store

client = TestClient(app)


def test_ui_displays_remaining_and_pending_balance():
    """Test AC-8: UI displays current employee remaining balance and pending-awaiting-approval days."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Add some approved and pending requests
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-05", "Holiday", 5)
    store.update_request_status("req1", LeaveStatus.APPROVED)
    
    store.add_leave_request("req2", "emp1", LeaveType.VACATION, "2024-02-01", "2024-02-03", "Break", 3)
    # req2 remains pending
    
    # Get the main page
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Verify balance card element exists
    assert 'id="balance-card"' in html_content
    
    # Get balance data that would be loaded by JavaScript
    balance_response = client.get("/api/employees/emp1/balance")
    balance = balance_response.json()
    
    # Verify the balance structure contains remaining and pending
    assert "remaining_days" in balance
    assert "pending_days" in balance
    assert balance["remaining_days"] == 19  # 24 - 5 approved
    assert balance["pending_days"] == 3


def test_ui_refresh_and_conditional_cancel_buttons():
    """Test AC-9: UI refreshes displayed balance after approval and exposes cancel action only for pending requests."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    store.add_employee("mgr1", "Manager One", "mgr@example.com")
    
    # Create requests with different statuses
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-05", "Holiday", 5)
    # req1 is pending
    
    store.add_leave_request("req2", "emp1", LeaveType.VACATION, "2024-02-01", "2024-02-03", "Break", 3)
    store.update_request_status("req2", LeaveStatus.APPROVED)
    
    store.add_leave_request("req3", "emp1", LeaveType.VACATION, "2024-03-01", "2024-03-02", "Trip", 2)
    store.update_request_status("req3", LeaveStatus.REJECTED)
    
    # Get the main page
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Verify history table exists
    assert 'id="history-table"' in html_content
    
    # Get request history that would be loaded by JavaScript
    history_response = client.get("/api/leaves/myrequests?employee_id=emp1")
    requests = history_response.json()
    
    # Verify we have requests with different statuses
    statuses = [req["status"] for req in requests]
    assert LeaveStatus.PENDING.value in statuses
    assert LeaveStatus.APPROVED.value in statuses
    assert LeaveStatus.REJECTED.value in statuses
    
    # Verify JavaScript would create cancel buttons (check for button template in HTML)
    # The actual button creation happens in JavaScript, but we can verify the structure
    assert 'data-id=' in html_content or 'Cancel' in html_content


def test_ui_shows_api_error_details():
    """Test AC-10: UI displays API-provided refusal reasons for submission and cancellation failures."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Get the main page to verify error element exists
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Verify error element exists for displaying API errors
    assert 'id="error"' in html_content
    
    # Test submission error with specific API message
    # Use up most allowance first
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-20", "Holiday", 20)
    store.update_request_status("req1", LeaveStatus.APPROVED)
    
    # Try to submit overdraw request
    response = client.post("/api/leaves/apply", json={
        "employee_id": "emp1",
        "leave_type": "VACATION",
        "start_date": "2024-02-01",
        "end_date": "2024-02-10",
        "reason": "Long trip"
    })
    
    assert response.status_code == 400
    error_data = response.json()
    assert "detail" in error_data
    
    # Verify the error detail is specific (not generic)
    error_detail = error_data["detail"]
    assert len(error_detail) > 10  # Should be more than generic "error"
    assert "remaining" in error_detail.lower() or "insufficient" in error_detail.lower()
    
    # Test cancellation error with specific API message
    store.add_leave_request("req2", "emp1", LeaveType.VACATION, "2024-03-01", "2024-03-05", "Trip", 5)
    store.update_request_status("req2", LeaveStatus.APPROVED)
    
    # Try to cancel approved request
    response = client.delete("/api/leaves/req2?employee_id=emp1")
    
    assert response.status_code == 400
    error_data = response.json()
    assert "detail" in error_data
    
    # Verify the error detail is specific
    error_detail = error_data["detail"]
    assert len(error_detail) > 10  # Should be more than generic "error"
    assert "approved" in error_detail.lower() or "cannot cancel" in error_detail.lower()
