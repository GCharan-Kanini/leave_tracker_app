import pytest
from fastapi.testclient import TestClient
from leave_tracker_app.main import app
from leave_tracker_app.models import LeaveRequest
from leave_tracker_app.views import request_list_view

client = TestClient(app)

def test_cancelled_request_shows_reason_in_list():
    """Test that cancelled requests display their cancellation reason in the list view."""
    # Create multiple leave requests with different statuses
    pending_request = LeaveRequest(
        id=1,
        employee_id=123,
        start_date="2024-01-10",
        end_date="2024-01-12",
        status="pending"
    )
    
    approved_request = LeaveRequest(
        id=2,
        employee_id=123,
        start_date="2024-02-05",
        end_date="2024-02-07",
        status="approved"
    )
    
    cancelled_request = LeaveRequest(
        id=3,
        employee_id=123,
        start_date="2024-03-15",
        end_date="2024-03-17",
        status="cancelled",
        cancellation_reason="Medical emergency in family"
    )
    
    # Get the leave request list page
    response = client.get("/leave-requests")
    
    # Assert successful response
    assert response.status_code == 200
    
    # Verify cancelled request shows its cancellation reason
    assert "Medical emergency in family" in response.text
    
    # Verify the reason appears near the cancelled request details
    response_text = response.text
    cancelled_section_start = response_text.find("2024-03-15")
    cancelled_section_end = response_text.find("</tr>", cancelled_section_start)
    cancelled_section = response_text[cancelled_section_start:cancelled_section_end]
    
    assert "cancelled" in cancelled_section.lower()
    assert "Medical emergency in family" in cancelled_section
    
    # Verify non-cancelled requests don't show cancellation reasons
    pending_section_start = response_text.find("2024-01-10")
    pending_section_end = response_text.find("</tr>", pending_section_start)
    pending_section = response_text[pending_section_start:pending_section_end]
    
    assert "Medical emergency in family" not in pending_section
    
    approved_section_start = response_text.find("2024-02-05")
    approved_section_end = response_text.find("</tr>", approved_section_start)
    approved_section = response_text[approved_section_start:approved_section_end]
    
    assert "Medical emergency in family" not in approved_section