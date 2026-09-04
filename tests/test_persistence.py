import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_database_path

client = TestClient(app)

def test_database_persistence():
    """Test data persists in SQLite database from environment variable"""
    # Check that database path comes from environment variable
    db_path = get_database_path()
    
    # Default should be leave_tracker.db if no env var set
    if "LEAVE_TRACKER_DB" not in os.environ:
        assert db_path == "leave_tracker.db"
    else:
        assert db_path == os.environ["LEAVE_TRACKER_DB"]
    
    # Create an employee
    employee_data = {
        "name": "Persistence Test",
        "email": "persistence@example.com",
        "role": "employee",
        "manager_id": None
    }
    
    response = client.post("/api/employees", json=employee_data)
    assert response.status_code == 201
    employee_id = response.json()["id"]
    
    # Verify data persists by retrieving balance
    balance_response = client.get(f"/api/employees/{employee_id}/balance")
    assert balance_response.status_code == 200
    balance = balance_response.json()
    assert "casual" in balance
    assert "sick" in balance
    assert "vacation" in balance

def test_temporary_database_for_tests():
    """Test that tests can point database to temporary file"""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        # Set environment variable to point to temp file
        original_db = os.environ.get("LEAVE_TRACKER_DB")
        os.environ["LEAVE_TRACKER_DB"] = temp_db_path
        
        # Verify the path is used
        db_path = get_database_path()
        assert db_path == temp_db_path
        
        # Test that we can create data in the temp database
        employee_data = {
            "name": "Temp DB Test",
            "email": "tempdb@example.com",
            "role": "employee",
            "manager_id": None
        }
        
        response = client.post("/api/employees", json=employee_data)
        assert response.status_code == 201
        
        # Verify the temp database file exists
        assert os.path.exists(temp_db_path)
        
    finally:
        # Restore original environment
        if original_db is not None:
            os.environ["LEAVE_TRACKER_DB"] = original_db
        elif "LEAVE_TRACKER_DB" in os.environ:
            del os.environ["LEAVE_TRACKER_DB"]
        
        # Clean up temp file
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
