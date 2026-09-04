import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_leave_types():
    """Test leave types endpoint lists types with yearly allowance"""
    response = client.get("/api/leave-types")
    assert response.status_code == 200
    leave_types = response.json()
    
    assert isinstance(leave_types, (list, dict))
    
    # Should contain the three main leave types
    if isinstance(leave_types, list):
        type_names = [lt.get("type") or lt.get("name") for lt in leave_types]
        assert "casual" in type_names
        assert "sick" in type_names
        assert "vacation" in type_names
    else:
        assert "casual" in leave_types
        assert "sick" in leave_types
        assert "vacation" in leave_types

def test_update_leave_type_allowance():
    """Test admin can update leave type allowance"""
    # Create admin user
    admin_data = {
        "name": "Admin User",
        "email": "admin@example.com",
        "role": "admin",
        "manager_id": None
    }
    admin_response = client.post("/api/employees", json=admin_data)
    assert admin_response.status_code == 201
    admin_id = admin_response.json()["id"]
    
    # Update leave type allowance
    update_data = {
        "allowance": 15,
        "admin_id": admin_id
    }
    
    response = client.put("/api/leave-types/casual", json=update_data)
    assert response.status_code == 200
    
    # Verify the update
    get_response = client.get("/api/leave-types")
    assert get_response.status_code == 200
    leave_types = get_response.json()
    
    # Check that casual allowance was updated
    if isinstance(leave_types, list):
        casual_type = next((lt for lt in leave_types if lt.get("type") == "casual" or lt.get("name") == "casual"), None)
        assert casual_type is not None
        assert casual_type.get("allowance") == 15
    else:
        assert leave_types["casual"] == 15

def test_update_leave_type_unauthorized():
    """Test non-admin cannot update leave type allowance"""
    # Create non-admin user
    employee_data = {
        "name": "Regular Employee",
        "email": "regular@example.com",
        "role": "employee",
        "manager_id": None
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Try to update leave type allowance
    update_data = {
        "allowance": 20,
        "admin_id": employee_id  # Not an admin
    }
    
    response = client.put("/api/leave-types/casual", json=update_data)
    assert response.status_code == 403

def test_get_summary_report():
    """Test admin can access summary report"""
    # Create admin user
    admin_data = {
        "name": "Report Admin",
        "email": "reportadmin@example.com",
        "role": "admin",
        "manager_id": None
    }
    admin_response = client.post("/api/employees", json=admin_data)
    assert admin_response.status_code == 201
    admin_id = admin_response.json()["id"]
    
    # Get summary report
    response = client.get(f"/api/reports/summary?admin_id={admin_id}")
    assert response.status_code == 200
    report = response.json()
    
    assert isinstance(report, (list, dict))
    
    # Report should contain per-employee totals by leave type
    if isinstance(report, list):
        for entry in report:
            assert "employee_id" in entry or "employee" in entry
            # Should have leave type totals
            assert any(key in entry for key in ["casual", "sick", "vacation", "totals", "approved_days"])

def test_get_summary_report_unauthorized():
    """Test non-admin cannot access summary report"""
    # Create non-admin user
    employee_data = {
        "name": "Regular Employee 2",
        "email": "regular2@example.com",
        "role": "employee",
        "manager_id": None
    }
    emp_response = client.post("/api/employees", json=employee_data)
    assert emp_response.status_code == 201
    employee_id = emp_response.json()["id"]
    
    # Try to get summary report
    response = client.get(f"/api/reports/summary?admin_id={employee_id}")
    assert response.status_code == 403
