import pytest
from fastapi.testclient import TestClient
from leave_tracker_app.main import app
from leave_tracker_app.models import LeaveRequest
from leave_tracker_app.forms import CancelRequestForm
from leave_tracker_app.views import cancel_request_view

client = TestClient(app)

def test_cancel_request_shows_reason_form():
    """Test that triggering cancel on a leave request presents a UI form asking for cancellation reason."""
    # Create a test leave request
    leave_request = LeaveRequest(
        id=1,
        employee_id=123,
        start_date="2024-01-15",
        end_date="2024-01-17",
        status="pending"
    )
    
    # Trigger cancel action
    response = client.get(f"/cancel-request/{leave_request.id}")
    
    # Assert that response contains cancellation reason form
    assert response.status_code == 200
    assert "cancellation_reason" in response.text
    assert "<form" in response.text
    assert "Cancel Request" in response.text

def test_cancel_with_empty_reason_rejected():
    """Test that submitting cancellation with empty reason is rejected with validation error."""
    # Create a test leave request
    leave_request = LeaveRequest(
        id=1,
        employee_id=123,
        start_date="2024-01-15",
        end_date="2024-01-17",
        status="pending"
    )
    
    # Submit cancellation with empty reason
    response = client.post(f"/cancel-request/{leave_request.id}", data={
        "cancellation_reason": ""
    })
    
    # Assert validation error is shown
    assert response.status_code == 400
    assert "Cancellation reason is required" in response.text
    
    # Verify request is not cancelled
    updated_request = LeaveRequest.get(leave_request.id)
    assert updated_request.status == "pending"
    assert not hasattr(updated_request, 'cancellation_reason') or updated_request.cancellation_reason is None

def test_failed_cancellation_preserves_state():
    """Test that request remains in original state when cancellation validation fails."""
    # Create a test leave request with specific state
    original_request = LeaveRequest(
        id=1,
        employee_id=123,
        start_date="2024-01-15",
        end_date="2024-01-17",
        status="approved",
        notes="Original notes"
    )
    
    # Capture original state
    original_status = original_request.status
    original_notes = original_request.notes
    
    # Submit invalid cancellation
    response = client.post(f"/cancel-request/{original_request.id}", data={
        "cancellation_reason": "   "  # whitespace only
    })
    
    # Assert validation failed
    assert response.status_code == 400
    
    # Verify all original properties are preserved
    preserved_request = LeaveRequest.get(original_request.id)
    assert preserved_request.status == original_status
    assert preserved_request.notes == original_notes
    assert preserved_request.employee_id == original_request.employee_id
    assert preserved_request.start_date == original_request.start_date
    assert preserved_request.end_date == original_request.end_date

def test_successful_cancellation_stores_reason():
    """Test that successful cancellation stores the provided reason with the request."""
    # Create a test leave request
    leave_request = LeaveRequest(
        id=1,
        employee_id=123,
        start_date="2024-01-15",
        end_date="2024-01-17",
        status="approved"
    )
    
    cancellation_reason = "Family emergency requires immediate attention"
    
    # Submit valid cancellation
    response = client.post(f"/cancel-request/{leave_request.id}", data={
        "cancellation_reason": cancellation_reason
    })
    
    # Assert successful cancellation
    assert response.status_code == 200
    
    # Verify request is cancelled and reason is stored
    cancelled_request = LeaveRequest.get(leave_request.id)
    assert cancelled_request.status == "cancelled"
    assert cancelled_request.cancellation_reason == cancellation_reason

def test_cancellation_reason_persists():
    """Test that stored cancellation reason remains available on subsequent reads."""
    # Create and cancel a leave request
    leave_request = LeaveRequest(
        id=1,
        employee_id=123,
        start_date="2024-01-15",
        end_date="2024-01-17",
        status="approved"
    )
    
    cancellation_reason = "Project deadline moved up unexpectedly"
    
    # Cancel the request
    client.post(f"/cancel-request/{leave_request.id}", data={
        "cancellation_reason": cancellation_reason
    })
    
    # Read the request multiple times to verify persistence
    first_read = LeaveRequest.get(leave_request.id)
    assert first_read.cancellation_reason == cancellation_reason
    
    second_read = LeaveRequest.get(leave_request.id)
    assert second_read.cancellation_reason == cancellation_reason
    
    # Verify reason persists across different access patterns
    all_requests = LeaveRequest.get_by_employee(leave_request.employee_id)
    cancelled_request = next(r for r in all_requests if r.id == leave_request.id)
    assert cancelled_request.cancellation_reason == cancellation_reason