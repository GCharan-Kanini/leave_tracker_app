import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_employee_view_element_ids():
    """Test Employee view contains required element IDs"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Required Employee view element IDs
    employee_ids = [
        "view-employee",
        "balance-card",
        "apply-form",
        "leave-type",
        "start-date",
        "end-date",
        "reason",
        "apply-submit",
        "history-table"
    ]
    
    for element_id in employee_ids:
        assert f'id="{element_id}"' in html_content, f"Missing element ID: {element_id}"

def test_manager_view_element_ids():
    """Test Manager view contains required element IDs"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Required Manager view element IDs
    manager_ids = [
        "view-manager",
        "pending-list",
        "team-calendar"
    ]
    
    for element_id in manager_ids:
        assert f'id="{element_id}"' in html_content, f"Missing element ID: {element_id}"
    
    # Check for approve/reject button patterns
    # These will have dynamic IDs like approve-<request_id>, reject-<request_id>
    assert "approve-" in html_content or "data-action=\"approve\"" in html_content
    assert "reject-" in html_content or "data-action=\"reject\"" in html_content

def test_admin_view_element_ids():
    """Test Admin view contains required element IDs"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Required Admin view element IDs
    admin_ids = [
        "view-admin",
        "employee-form",
        "employee-list",
        "leave-types",
        "summary-report"
    ]
    
    for element_id in admin_ids:
        assert f'id="{element_id}"' in html_content, f"Missing element ID: {element_id}"

def test_error_element_id():
    """Test UI contains error element with ID 'error'"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text

    assert 'id="error"' in html_content, "Missing error element ID"


def test_inline_cancellation_control_markers_present():
    """Test served page exposes inline cancellation control markers."""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text

    assert 'id="cancel-123"' in html_content
    assert 'id="cancel-controls-123"' in html_content
    assert 'id="cancel-reason-123"' in html_content
    assert 'id="confirm-cancel-123"' in html_content
    assert 'disabled' in html_content.lower()
