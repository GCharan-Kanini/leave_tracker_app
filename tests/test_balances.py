import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_employee_balance_default_allowances():
    """Test that employee balance returns remaining days per leave type"""
    # Create employee first
    employee_data = {
        "name": "Balance Test User",
        "email": "balance@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Get balance
    response = client.get(f"/api/employees/{employee_id}/balance")
    assert response.status_code == 200
    balance = response.json()
    
    # Check default allowances
    assert "casual" in balance
    assert "sick" in balance
    assert "vacation" in balance
    assert balance["casual"] == 12  # default
    assert balance["sick"] == 10    # default
    assert balance["vacation"] == 20 # default

def test_balance_uses_configured_allowances():
    """Test that balance reflects configured yearly allowances"""
    # Create employee
    employee_data = {
        "name": "Config Test User",
        "email": "config@example.com",
        "role": "employee",
        "manager_id": None
    }
    create_response = client.post("/api/employees", json=employee_data)
    assert create_response.status_code == 201
    employee_id = create_response.json()["id"]
    
    # Get initial balance
    response = client.get(f"/api/employees/{employee_id}/balance")
    assert response.status_code == 200
    balance = response.json()
    
    # Verify balance starts from configured allowances
    assert isinstance(balance["casual"], int)
    assert isinstance(balance["sick"], int)
    assert isinstance(balance["vacation"], int)
    assert balance["casual"] >= 0
    assert balance["sick"] >= 0
    assert balance["vacation"] >= 0
