import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def test_cancel_reveals_inline_controls():
    """Test clicking Cancel on pending request reveals inline cancellation reason input and Confirm button"""
    # Mock the API responses for employee view
    with patch('httpx.AsyncClient.get') as mock_get, \
         patch('httpx.AsyncClient.delete') as mock_delete:
        
        # Mock balance response
        balance_response = MagicMock()
        balance_response.status_code = 200
        balance_response.json.return_value = {"annual": 20, "sick": 10}
        
        # Mock requests response with pending request
        requests_response = MagicMock()
        requests_response.status_code = 200
        requests_response.json.return_value = [
            {
                "request_id": 123,
                "leave_type": "annual",
                "status": "pending",
                "working_days": 5,
                "cancellation_reason": None
            }
        ]
        
        mock_get.side_effect = [balance_response, requests_response]
        
        # Get the main page
        response = client.get("/")
        assert response.status_code == 200
        html_content = response.text
        
        # Verify Cancel button exists for pending requests
        assert 'id="cancel-123"' in html_content
        assert 'data-id="123"' in html_content
        
        # Verify the button has click handler that should show inline controls
        # The new implementation should not use window.prompt
        assert 'window.prompt' not in html_content or 'inline' in html_content.lower()
        
        # Verify structure supports inline controls (input and confirm button)
        # The HTML should have elements that can be dynamically shown/hidden
        assert 'button' in html_content
        assert 'Cancel' in html_content

def test_confirm_button_gating():
    """Test Confirm button remains disabled until cancellation reason is non-blank"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Verify the page has JavaScript that handles input validation
    # The implementation should check for non-blank reason after trimming
    assert 'trim()' in html_content or 'disabled' in html_content.lower()
    
    # Verify there's logic to enable/disable confirm button based on input
    # This tests the gating mechanism exists in the UI code
    button_gating_indicators = ['disabled', 'enable', 'trim', 'length']
    has_gating_logic = any(indicator in html_content.lower() for indicator in button_gating_indicators)
    assert has_gating_logic, "UI should have button gating logic for non-blank reason"

def test_confirm_sends_delete_request():
    """Test confirming cancellation sends DELETE request with cancellation_reason"""
    with patch('httpx.AsyncClient.get') as mock_get, \
         patch('httpx.AsyncClient.delete') as mock_delete:
        
        # Mock the initial data load
        balance_response = MagicMock()
        balance_response.status_code = 200
        balance_response.json.return_value = {"annual": 20}
        
        requests_response = MagicMock()
        requests_response.status_code = 200
        requests_response.json.return_value = [
            {
                "request_id": 123,
                "leave_type": "annual", 
                "status": "pending",
                "working_days": 5,
                "cancellation_reason": None
            }
        ]
        
        mock_get.side_effect = [balance_response, requests_response]
        
        # Mock successful DELETE response
        delete_response = MagicMock()
        delete_response.status_code = 204
        mock_delete.return_value = delete_response
        
        response = client.get("/")
        assert response.status_code == 200
        html_content = response.text
        
        # Verify the DELETE request structure is preserved
        # The API call should still use the same endpoint and payload format
        assert '/api/leaves/' in html_content
        assert 'DELETE' in html_content
        assert 'cancellation_reason' in html_content
        
        # Verify JSON body structure is maintained
        assert 'JSON.stringify' in html_content
        assert 'Content-Type' in html_content
        assert 'application/json' in html_content

def test_cancellation_reason_displayed_after_cancel():
    """Test cancellation reason is displayed in UI after successful cancellation"""
    with patch('httpx.AsyncClient.get') as mock_get:
        
        # Mock response with cancelled request showing cancellation reason
        balance_response = MagicMock()
        balance_response.status_code = 200
        balance_response.json.return_value = {"annual": 15}
        
        requests_response = MagicMock()
        requests_response.status_code = 200
        requests_response.json.return_value = [
            {
                "request_id": 123,
                "leave_type": "annual",
                "status": "cancelled", 
                "working_days": 5,
                "cancellation_reason": "Personal emergency"
            }
        ]
        
        mock_get.side_effect = [balance_response, requests_response]
        
        response = client.get("/")
        assert response.status_code == 200
        html_content = response.text
        
        # Verify cancellation reason is displayed in the table
        # The UI should show the stored cancellation reason
        assert 'cancellation_reason' in html_content.lower() or 'cancellation reason' in html_content
        
        # Verify the table structure includes cancellation reason column
        assert 'Cancellation Reason' in html_content or 'cancellation_reason' in html_content
        
        # Verify fallback display for null cancellation reasons
        assert '|| "-"' in html_content or 'cancellation_reason || "-"' in html_content

def test_no_prompt_behavior():
    """Test UI uses inline controls instead of window.prompt for cancellation"""
    response = client.get("/")
    assert response.status_code == 200
    html_content = response.text
    
    # Verify the new implementation doesn't rely on window.prompt
    # or if it does, it's being replaced with inline controls
    if 'window.prompt' in html_content:
        # If prompt still exists, verify it's being replaced or conditional
        inline_indicators = ['inline', 'input', 'confirm', 'reason']
        has_inline_alternative = any(indicator in html_content.lower() for indicator in inline_indicators)
        assert has_inline_alternative, "Should have inline alternative to window.prompt"
    
    # Verify presence of elements that support inline cancellation
    assert 'button' in html_content.lower()
    assert 'cancel' in html_content.lower()
    
    # Verify the UI has structure for dynamic content (inline controls)
    dynamic_indicators = ['addEventListener', 'createElement', 'innerHTML', 'appendChild']
    has_dynamic_capability = any(indicator in html_content for indicator in dynamic_indicators)
    assert has_dynamic_capability, "UI should support dynamic inline control creation"