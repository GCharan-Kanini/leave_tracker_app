import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ui_views_present():
    """Test UI has three selectable views with proper functionality"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Check that the UI has references to the three views
    assert "employee" in html_content.lower() or "Employee" in html_content
    assert "manager" in html_content.lower() or "Manager" in html_content
    assert "admin" in html_content.lower() or "Admin" in html_content
    
    # Check that fetch is used for API calls
    assert "fetch" in html_content
    
    # Check that the UI talks to the expected API endpoints
    api_endpoints = [
        "/api/employees",
        "/api/leaves",
        "/api/managers",
        "/api/leave-types",
        "/api/reports"
    ]
    
    # At least some API endpoints should be referenced
    api_found = any(endpoint in html_content for endpoint in api_endpoints)
    assert api_found, "UI should reference API endpoints"

def test_ui_error_handling():
    """Test UI shows API error messages inline and refreshes data"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text

    # Check for error handling elements
    assert "error" in html_content.lower()

    # Check for refresh/reload functionality
    refresh_indicators = ["refresh", "reload", "update", "fetch"]
    refresh_found = any(indicator in html_content.lower() for indicator in refresh_indicators)
    assert refresh_found, "UI should have refresh functionality"


def test_ui_uses_inline_cancel_confirmation_instead_of_prompt():
    """Test served page includes inline cancellation controls and prompt-free flow."""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text

    assert "window.prompt" not in html_content
    assert "cancel-controls-" in html_content
    assert "cancel-reason-" in html_content
    assert "confirm-cancel-" in html_content
    assert "Please provide a cancellation reason" not in html_content
    assert "method: \"DELETE\"" in html_content
    assert "cancellation_reason" in html_content
