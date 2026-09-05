import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta

client = TestClient(app)

def test_cancel_leave_requires_reason():
    """Test that cancelling a leave request requires a cancellation reason and fails without one"""
    # Create employee
    employee_data = {
        "name": "Cancel Reason Test User",
        "email": "cancelreason@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "To be cancelled without reason"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Try to cancel without providing cancellation reason
    cancel_response = client.delete(f"/api/leaves/{request_id}?employee_id={employee_id}")
    assert cancel_response.status_code == 422
    
    # Verify request is still pending (not cancelled)
    history_response = client.get(f"/api/leaves/myrequests?employee_id={employee_id}")
    assert history_response.status_code == 200
    requests = history_response.json()
    assert len(requests) == 1
    assert requests[0]["status"] == "pending"

def test_cancel_leave_with_reason_succeeds():
    """Test that cancelling a leave request succeeds when cancellation reason is provided"""
    # Create employee
    employee_data = {
        "name": "Cancel With Reason User",
        "email": "cancelwithreason@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "To be cancelled with reason"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Cancel with cancellation reason
    cancel_data = {
        "cancellation_reason": "Change of plans"
    }
    cancel_response = client.delete(
        f"/api/leaves/{request_id}?employee_id={employee_id}",
        json=cancel_data
    )
    assert cancel_response.status_code == 200
    
    # Verify request is cancelled
    history_response = client.get(f"/api/leaves/myrequests?employee_id={employee_id}")
    assert history_response.status_code == 200
    requests = history_response.json()
    assert len(requests) == 1
    assert requests[0]["status"] == "cancelled"

def test_cancellation_reason_persisted():
    """Test that cancellation reason is persisted with the leave request in backend storage"""
    # Create employee
    employee_data = {
        "name": "Persist Reason User",
        "email": "persistreason@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Original reason"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Cancel with specific cancellation reason
    cancellation_reason = "Family emergency came up"
    cancel_data = {
        "cancellation_reason": cancellation_reason
    }
    cancel_response = client.delete(
        f"/api/leaves/{request_id}?employee_id={employee_id}",
        json=cancel_data
    )
    assert cancel_response.status_code == 200
    
    # Verify cancellation reason is stored by checking database directly
    from app.db import get_connection
    with get_connection() as connection:
        row = connection.execute(
            "SELECT cancellation_reason FROM leave_requests WHERE id = ?",
            (request_id,)
        ).fetchone()
        assert row is not None
        assert row["cancellation_reason"] == cancellation_reason

def test_leave_history_shows_cancellation_reason():
    """Test that employee leave history shows cancellation reason for cancelled requests"""
    # Create employee
    employee_data = {
        "name": "History Reason User",
        "email": "historyreason@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Original reason"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Cancel with cancellation reason
    cancellation_reason = "Project deadline moved"
    cancel_data = {
        "cancellation_reason": cancellation_reason
    }
    cancel_response = client.delete(
        f"/api/leaves/{request_id}?employee_id={employee_id}",
        json=cancel_data
    )
    assert cancel_response.status_code == 200
    
    # Get leave history and verify cancellation reason is included
    history_response = client.get(f"/api/leaves/myrequests?employee_id={employee_id}")
    assert history_response.status_code == 200
    requests = history_response.json()
    
    assert len(requests) == 1
    cancelled_request = requests[0]
    assert cancelled_request["status"] == "cancelled"
    assert "cancellation_reason" in cancelled_request
    assert cancelled_request["cancellation_reason"] == cancellation_reason