import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_employee_success():
    """Test creating employee with valid data"""
    employee_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "employee",
        "manager_id": None
    }
    response = client.post("/api/employees", json=employee_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john.doe@example.com"
    assert data["role"] == "employee"
    assert "id" in data

def test_create_employee_duplicate_email():
    """Test that duplicate email returns 409"""
    employee_data = {
        "name": "Jane Doe",
        "email": "duplicate@example.com",
        "role": "employee",
        "manager_id": None
    }
    # Create first employee
    response1 = client.post("/api/employees", json=employee_data)
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = client.post("/api/employees", json=employee_data)
    assert response2.status_code == 409

def test_create_employee_invalid_role():
    """Test that invalid role returns 422 naming the value"""
    employee_data = {
        "name": "Invalid Role User",
        "email": "invalid@example.com",
        "role": "invalid_role",
        "manager_id": None
    }
    response = client.post("/api/employees", json=employee_data)
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert "invalid_role" in str(error_detail)
