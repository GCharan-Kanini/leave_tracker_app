import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta

client = TestClient(app)

def test_apply_leave_success():
    """Test leave application creates pending request with working days calculation"""
    # Create employee
    employee_data = {
        "name": "Leave Test User",
        "email": "leave@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Apply for leave
    start_date = datetime.now().date() + timedelta(days=1)
    end_date = start_date + timedelta(days=2)  # 3 days total, but weekends excluded
    
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "reason": "Personal work"
    }
    
    response = client.post("/api/leaves/apply", json=leave_data)
    assert response.status_code == 201
    data = response.json()
    
    assert "request_id" in data
    assert data["status"] == "pending"
    assert "working_days" in data
    assert isinstance(data["working_days"], int)
    assert data["working_days"] > 0

def test_apply_leave_invalid_date_range():
    """Test that end date before start date returns 422"""
    # Create employee
    employee_data = {
        "name": "Date Test User",
        "email": "datetest@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Apply with invalid date range
    start_date = datetime.now().date() + timedelta(days=5)
    end_date = start_date - timedelta(days=1)  # End before start
    
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "reason": "Invalid dates"
    }
    
    response = client.post("/api/leaves/apply", json=leave_data)
    assert response.status_code == 422

def test_apply_leave_insufficient_balance():
    """Test requesting more days than balance returns 422 with remaining balance"""
    # Create employee
    employee_data = {
        "name": "Balance Test User",
        "email": "balancetest@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Apply for excessive leave (more than 12 casual days)
    start_date = datetime.now().date() + timedelta(days=1)
    end_date = start_date + timedelta(days=20)  # More than casual allowance
    
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "reason": "Too many days"
    }
    
    response = client.post("/api/leaves/apply", json=leave_data)
    assert response.status_code == 422
    error_detail = str(response.json()["detail"])
    assert "balance" in error_detail.lower() or "remaining" in error_detail.lower()

def test_apply_leave_unknown_employee():
    """Test that unknown employee returns 404"""
    leave_data = {
        "employee_id": 99999,  # Non-existent employee
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Unknown employee test"
    }
    
    response = client.post("/api/leaves/apply", json=leave_data)
    assert response.status_code == 404

def test_get_my_requests():
    """Test employee can retrieve their leave requests newest first"""
    # Create employee
    employee_data = {
        "name": "History Test User",
        "email": "history@example.com",
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
        "reason": "Test leave"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    
    # Get requests
    response = client.get(f"/api/leaves/myrequests?employee_id={employee_id}")
    assert response.status_code == 200
    requests = response.json()
    
    assert isinstance(requests, list)
    if len(requests) > 0:
        request = requests[0]
        assert "status" in request
        assert "working_days" in request or "requested_days" in request

def test_cancel_leave_success():
    """Test employee can cancel their pending request"""
    # Create employee
    employee_data = {
        "name": "Cancel Test User",
        "email": "cancel@example.com",
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
        "reason": "To be cancelled"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Cancel the request
    response = client.delete(
        f"/api/leaves/{request_id}?employee_id={employee_id}",
        json={"cancellation_reason": "No longer needed"},
    )
    assert response.status_code == 200

def test_cancel_leave_not_pending():
    """Test canceling non-pending request returns 409"""
    # Create employee and manager
    manager_data = {
        "name": "Manager User",
        "email": "manager@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager_response = client.post("/api/employees", json=manager_data)
    assert manager_response.status_code == 201
    manager_id = manager_response.json()["id"]
    
    employee_data = {
        "name": "Cancel Test User 2",
        "email": "cancel2@example.com",
        "role": "employee",
        "manager_id": manager_id
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
        "reason": "To be approved then cancelled"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Approve the request
    approve_response = client.put(f"/api/leaves/{request_id}/approve", json={"manager_id": manager_id})
    assert approve_response.status_code == 200
    
    # Try to cancel approved request
    response = client.delete(
        f"/api/leaves/{request_id}?employee_id={employee_id}",
        json={"cancellation_reason": "Need to revert approved leave"},
    )
    assert response.status_code == 409

def test_cancel_leave_not_owner():
    """Test canceling request not owned by employee returns 403"""
    # Create two employees
    employee1_data = {
        "name": "Employee 1",
        "email": "emp1@example.com",
        "role": "employee",
        "manager_id": None
    }
    emp1_response = client.post("/api/employees", json=employee1_data)
    assert emp1_response.status_code == 201
    employee1_id = emp1_response.json()["id"]
    
    employee2_data = {
        "name": "Employee 2",
        "email": "emp2@example.com",
        "role": "employee",
        "manager_id": None
    }
    emp2_response = client.post("/api/employees", json=employee2_data)
    assert emp2_response.status_code == 201
    employee2_id = emp2_response.json()["id"]
    
    # Employee 1 applies for leave
    leave_data = {
        "employee_id": employee1_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Employee 1 leave"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Employee 2 tries to cancel Employee 1's request
    response = client.delete(
        f"/api/leaves/{request_id}?employee_id={employee2_id}",
        json={"cancellation_reason": "Not my leave"},
    )
    assert response.status_code == 403
