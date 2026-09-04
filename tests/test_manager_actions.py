import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta

client = TestClient(app)

def test_approve_leave_success():
    """Test manager can approve pending leave request and deduct days from balance"""
    # Create manager
    manager_data = {
        "name": "Manager User",
        "email": "manager@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager_response = client.post("/api/employees", json=manager_data)
    assert manager_response.status_code == 201
    manager_id = manager_response.json()["id"]
    
    # Create employee under manager
    employee_data = {
        "name": "Employee User",
        "email": "employee@example.com",
        "role": "employee",
        "manager_id": manager_id
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Get initial balance
    balance_response = client.get(f"/api/employees/{employee_id}/balance")
    assert balance_response.status_code == 200
    initial_balance = balance_response.json()["casual"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Manager approval test"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    working_days = apply_response.json()["working_days"]
    
    # Manager approves
    approve_response = client.put(f"/api/leaves/{request_id}/approve", json={"manager_id": manager_id})
    assert approve_response.status_code == 200
    
    # Check balance is deducted
    new_balance_response = client.get(f"/api/employees/{employee_id}/balance")
    assert new_balance_response.status_code == 200
    new_balance = new_balance_response.json()["casual"]
    assert new_balance == initial_balance - working_days

def test_reject_leave_success():
    """Test manager can reject pending leave request and leave balance unchanged"""
    # Create manager
    manager_data = {
        "name": "Manager User 2",
        "email": "manager2@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager_response = client.post("/api/employees", json=manager_data)
    assert manager_response.status_code == 201
    manager_id = manager_response.json()["id"]
    
    # Create employee under manager
    employee_data = {
        "name": "Employee User 2",
        "email": "employee2@example.com",
        "role": "employee",
        "manager_id": manager_id
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Get initial balance
    balance_response = client.get(f"/api/employees/{employee_id}/balance")
    assert balance_response.status_code == 200
    initial_balance = balance_response.json()["casual"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Manager rejection test"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Manager rejects
    reject_response = client.put(f"/api/leaves/{request_id}/reject", json={"manager_id": manager_id})
    assert reject_response.status_code == 200
    
    # Check balance is unchanged
    new_balance_response = client.get(f"/api/employees/{employee_id}/balance")
    assert new_balance_response.status_code == 200
    new_balance = new_balance_response.json()["casual"]
    assert new_balance == initial_balance

def test_approve_leave_unauthorized():
    """Test only employee's manager or admin can approve"""
    # Create two managers
    manager1_data = {
        "name": "Manager 1",
        "email": "manager1@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager1_response = client.post("/api/employees", json=manager1_data)
    assert manager1_response.status_code == 201
    manager1_id = manager1_response.json()["id"]
    
    manager2_data = {
        "name": "Manager 2",
        "email": "manager2@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager2_response = client.post("/api/employees", json=manager2_data)
    assert manager2_response.status_code == 201
    manager2_id = manager2_response.json()["id"]
    
    # Create employee under manager1
    employee_data = {
        "name": "Employee Under Manager1",
        "email": "emp_mgr1@example.com",
        "role": "employee",
        "manager_id": manager1_id
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Unauthorized approval test"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Manager2 (not the employee's manager) tries to approve
    approve_response = client.put(f"/api/leaves/{request_id}/approve", json={"manager_id": manager2_id})
    assert approve_response.status_code == 403

def test_approve_leave_not_pending():
    """Test acting on non-pending request returns 409"""
    # Create manager
    manager_data = {
        "name": "Manager User 3",
        "email": "manager3@example.com",
        "role": "manager",
        "manager_id": None
    }
    manager_response = client.post("/api/employees", json=manager_data)
    assert manager_response.status_code == 201
    manager_id = manager_response.json()["id"]
    
    # Create employee under manager
    employee_data = {
        "name": "Employee User 3",
        "email": "employee3@example.com",
        "role": "employee",
        "manager_id": manager_id
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Apply for leave
    leave_data = {
        "employee_id": employee_id,
        "leave_type": "casual",
        "start_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
        "reason": "Double approval test"
    }
    
    apply_response = client.post("/api/leaves/apply", json=leave_data)
    assert apply_response.status_code == 201
    request_id = apply_response.json()["request_id"]
    
    # Manager approves first time
    approve_response1 = client.put(f"/api/leaves/{request_id}/approve", json={"manager_id": manager_id})
    assert approve_response1.status_code == 200
    
    # Manager tries to approve again
    approve_response2 = client.put(f"/api/leaves/{request_id}/approve", json={"manager_id": manager_id})
    assert approve_response2.status_code == 409
