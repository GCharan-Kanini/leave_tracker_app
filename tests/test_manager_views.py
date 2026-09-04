import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta

client = TestClient(app)

def test_get_pending_requests():
    """Test manager can view pending requests from direct reports"""
    # Create manager
    manager_data = {
        "name": "Manager Views",
        "email": "managerviews@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager_response = client.post("/api/employees", json=manager_data)
    assert manager_response.status_code == 201
    manager_id = manager_response.json()["id"]
    
    # Create employee under manager
    employee_data = {
        "name": "Direct Report",
        "email": "directreport@example.com",
        "role": "employee",
        "manager_id": manager_id
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Employee applies for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Pending request test"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    
    # Manager gets pending requests
    response = client.get(f"/api/managers/{manager_id}/pending")
    assert response.status_code == 200
    pending_requests = response.json()
    
    assert isinstance(pending_requests, list)
    # Should have at least the request we just created
    assert len(pending_requests) >= 1
    
    # Check structure of pending request
    if len(pending_requests) > 0:
        request = pending_requests[0]
        assert "employee_id" in request or "id" in request
        assert "status" in request or request.get("status") == "pending"

def test_get_team_calendar():
    """Test manager can view team calendar for specific month"""
    # Create manager
    manager_data = {
        "name": "Calendar Manager",
        "email": "calendarmanager@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager_response = client.post("/api/employees", json=manager_data)
    assert manager_response.status_code == 201
    manager_id = manager_response.json()["id"]
    
    # Create employee under manager
    employee_data = {
        "name": "Calendar Employee",
        "email": "calendaremployee@example.com",
        "role": "employee",
        "manager_id": manager_id
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Apply and approve leave for current month
    current_month = datetime.now().strftime("%Y-%m")
    start_date = datetime.now().date() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)
    
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "vacation",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "reason": "Calendar test leave"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Approve the leave
    approve_response = client.put(f"/api/leaves/{request_id}/approve", json={"manager_id": manager_id})
    assert approve_response.status_code == 200
    
    # Get team calendar
    response = client.get(f"/api/managers/{manager_id}/calendar?month={current_month}")
    assert response.status_code == 200
    calendar_entries = response.json()
    
    assert isinstance(calendar_entries, list)
    
    # Check structure of calendar entries
    for entry in calendar_entries:
        assert "employee_id" in entry
        assert "name" in entry
        assert "start_date" in entry
        assert "end_date" in entry
        assert "leave_type" in entry
