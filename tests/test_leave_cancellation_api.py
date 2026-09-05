"""Tests for leave request cancellation API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app import app
from leave_tracker.models import LeaveStatus, LeaveType
from leave_tracker.store import store

client = TestClient(app)


def test_employee_can_cancel_pending_request():
    """Test AC-5: Employee can cancel their own request only while it is pending."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Create pending request
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-05", "Holiday", 5)
    
    # Verify initial status
    request = store.get_request("req1")
    assert request.status == LeaveStatus.PENDING.value
    
    # Cancel the request
    response = client.delete("/api/leaves/req1?employee_id=emp1")
    
    # Should succeed
    assert response.status_code == 204
    
    # Verify status changed to cancelled
    updated_request = store.get_request("req1")
    assert updated_request.status == LeaveStatus.CANCELLED.value


def test_non_pending_cancellation_refused_no_mutation():
    """Test AC-6: Cancellation attempts for approved/rejected/cancelled requests are refused with clear reasons and do not alter request state."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Test approved request cancellation
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-05", "Holiday", 5)
    store.update_request_status("req1", LeaveStatus.APPROVED)
    
    response = client.delete("/api/leaves/req1?employee_id=emp1")
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    assert "approved" in error_detail.lower() or "cannot cancel" in error_detail.lower()
    
    # Verify state unchanged
    request = store.get_request("req1")
    assert request.status == LeaveStatus.APPROVED.value
    
    # Test rejected request cancellation
    store.add_leave_request("req2", "emp1", LeaveType.VACATION, "2024-02-01", "2024-02-05", "Break", 5)
    store.update_request_status("req2", LeaveStatus.REJECTED)
    
    response = client.delete("/api/leaves/req2?employee_id=emp1")
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    assert "rejected" in error_detail.lower() or "cannot cancel" in error_detail.lower()
    
    # Verify state unchanged
    request = store.get_request("req2")
    assert request.status == LeaveStatus.REJECTED.value
    
    # Test already cancelled request cancellation
    store.add_leave_request("req3", "emp1", LeaveType.VACATION, "2024-03-01", "2024-03-05", "Trip", 5)
    store.update_request_status("req3", LeaveStatus.CANCELLED)
    
    response = client.delete("/api/leaves/req3?employee_id=emp1")
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    assert "cancelled" in error_detail.lower() or "cannot cancel" in error_detail.lower()
    
    # Verify state unchanged
    request = store.get_request("req3")
    assert request.status == LeaveStatus.CANCELLED.value


def test_cancelled_requests_visible_in_history():
    """Test AC-7: Cancelled requests remain visible in request listings with cancelled status."""
    store.clear()
    store.add_employee("emp1", "John Doe", "john@example.com")
    
    # Create and cancel a request
    store.add_leave_request("req1", "emp1", LeaveType.VACATION, "2024-01-01", "2024-01-05", "Holiday", 5)
    store.update_request_status("req1", LeaveStatus.CANCELLED)
    
    # Create other requests for comparison
    store.add_leave_request("req2", "emp1", LeaveType.VACATION, "2024-02-01", "2024-02-05", "Break", 5)
    store.add_leave_request("req3", "emp1", LeaveType.VACATION, "2024-03-01", "2024-03-05", "Trip", 5)
    store.update_request_status("req3", LeaveStatus.APPROVED)
    
    # Get request history
    response = client.get("/api/leaves/myrequests?employee_id=emp1")
    assert response.status_code == 200
    
    requests = response.json()
    request_ids = [req["request_id"] for req in requests]
    
    # Cancelled request should be visible
    assert "req1" in request_ids
    
    # Find cancelled request in response
    cancelled_request = next(req for req in requests if req["request_id"] == "req1")
    assert cancelled_request["status"] == LeaveStatus.CANCELLED.value
