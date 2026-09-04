import pytest
from datetime import date

def test_add_employee_success():
    """Test that add_employee successfully registers an employee."""
    try:
        from leave_tracker.tracker import LeaveTracker
    except (ImportError, AttributeError):
        LeaveTracker = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    
    tracker = LeaveTracker()
    
    # Add employee without manager
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    
    # Add employee with manager
    tracker.add_employee('emp2', 'Jane Smith', 'jane@example.com', manager_id='emp1')
    
    # Verify employees were added (implementation detail may vary, but should not raise)
    # The fact that no exception was raised indicates success

def test_add_employee_duplicate_raises_error():
    """Test that adding duplicate employee ID raises DuplicateEmployeeError."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import DuplicateEmployeeError
    except (ImportError, AttributeError):
        LeaveTracker = None
        DuplicateEmployeeError = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert DuplicateEmployeeError is not None, 'leave_tracker.models.DuplicateEmployeeError is not implemented yet'
    
    tracker = LeaveTracker()
    
    # Add employee first time
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    
    # Store state before duplicate attempt
    state_before = str(tracker.__dict__) if hasattr(tracker, '__dict__') else None
    
    # Attempt to add same employee ID should raise DuplicateEmployeeError
    with pytest.raises(DuplicateEmployeeError):
        tracker.add_employee('emp1', 'Different Name', 'different@example.com')
    
    # Verify tracker state unchanged after failed operation
    state_after = str(tracker.__dict__) if hasattr(tracker, '__dict__') else None
    assert state_after == state_before, 'Tracker state changed after failed duplicate employee addition'

def test_balance_operations_success():
    """Test that set_balance and get_balance work for valid employee."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    
    # Set and get balance
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    
    assert balance == 10, f'Expected balance 10, got {balance}'
    
    # Set different balance for different leave type
    tracker.set_balance('emp1', LeaveType.SICK, 5)
    sick_balance = tracker.get_balance('emp1', LeaveType.SICK)
    casual_balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    
    assert sick_balance == 5, f'Expected sick balance 5, got {sick_balance}'
    assert casual_balance == 10, f'Casual balance should remain 10, got {casual_balance}'

def test_balance_operations_unknown_employee():
    """Test that balance operations raise UnknownEmployeeError for invalid employee."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType, UnknownEmployeeError
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
        UnknownEmployeeError = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    assert UnknownEmployeeError is not None, 'leave_tracker.models.UnknownEmployeeError is not implemented yet'
    
    tracker = LeaveTracker()
    
    # Test set_balance with unknown employee
    with pytest.raises(UnknownEmployeeError):
        tracker.set_balance('unknown', LeaveType.CASUAL, 10)
    
    # Test get_balance with unknown employee
    with pytest.raises(UnknownEmployeeError):
        tracker.get_balance('unknown', LeaveType.CASUAL)

def test_apply_leave_success():
    """Test that apply returns LeaveRequest with PENDING status and unique request_id."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    
    assert request is not None, 'apply should return a LeaveRequest object'
    assert hasattr(request, 'status'), 'LeaveRequest should have status attribute'
    assert hasattr(request, 'request_id'), 'LeaveRequest should have request_id attribute'
    
    assert request.status == 'PENDING', f'Expected status PENDING, got {request.status}'
    assert request.request_id is not None, 'request_id should not be None'
    
    # Test uniqueness of request IDs
    request2 = tracker.apply('emp1', LeaveType.CASUAL, date(2024, 2, 1), date(2024, 2, 2), 'Another leave')
    assert request2.request_id != request.request_id, 'Request IDs should be unique'

def test_apply_leave_invalid_date_range():
    """Test that end_date before start_date raises ValueError."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    # Store state before invalid operation
    state_before = str(tracker.__dict__) if hasattr(tracker, '__dict__') else None
    
    start_date = date(2024, 1, 5)
    end_date = date(2024, 1, 3)  # Before start_date
    
    with pytest.raises(ValueError):
        tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Invalid dates')
    
    # Verify tracker state unchanged after failed operation
    state_after = str(tracker.__dict__) if hasattr(tracker, '__dict__') else None
    assert state_after == state_before, 'Tracker state changed after failed apply with invalid dates'

def test_apply_leave_insufficient_balance():
    """Test that insufficient balance raises InsufficientBalanceError."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType, InsufficientBalanceError
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
        InsufficientBalanceError = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    assert InsufficientBalanceError is not None, 'leave_tracker.models.InsufficientBalanceError is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 2)  # Only 2 days available
    
    # Store state before invalid operation
    state_before = str(tracker.__dict__) if hasattr(tracker, '__dict__') else None
    balance_before = tracker.get_balance('emp1', LeaveType.CASUAL)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 5)  # 5 days, but only 2 available
    
    with pytest.raises(InsufficientBalanceError):
        tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Too many days')
    
    # Verify tracker state and balance unchanged after failed operation
    state_after = str(tracker.__dict__) if hasattr(tracker, '__dict__') else None
    balance_after = tracker.get_balance('emp1', LeaveType.CASUAL)
    
    assert state_after == state_before, 'Tracker state changed after failed apply with insufficient balance'
    assert balance_after == balance_before, 'Balance changed after failed apply with insufficient balance'

def test_approve_leave_success():
    """Test that manager can approve employee's leave request."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('manager1', 'Manager One', 'manager@example.com')
    tracker.add_employee('emp1', 'John Doe', 'john@example.com', manager_id='manager1')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)  # 3 days
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    initial_balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    
    # Manager approves the request
    tracker.approve(request.request_id, 'manager1')
    
    # Verify status changed to APPROVED
    assert request.status == 'APPROVED', f'Expected status APPROVED, got {request.status}'
    
    # Verify balance was deducted
    final_balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    expected_balance = initial_balance - 3  # 3 days deducted
    assert final_balance == expected_balance, f'Expected balance {expected_balance}, got {final_balance}'

def test_approve_leave_not_authorized():
    """Test that non-manager cannot approve leave request."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType, NotAuthorizedError
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
        NotAuthorizedError = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    assert NotAuthorizedError is not None, 'leave_tracker.models.NotAuthorizedError is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('manager1', 'Manager One', 'manager@example.com')
    tracker.add_employee('emp1', 'John Doe', 'john@example.com', manager_id='manager1')
    tracker.add_employee('emp2', 'Jane Smith', 'jane@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    initial_status = request.status
    initial_balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    
    # Non-manager tries to approve
    with pytest.raises(NotAuthorizedError):
        tracker.approve(request.request_id, 'emp2')
    
    # Verify request status unchanged
    assert request.status == initial_status, 'Request status changed after unauthorized approve attempt'
    
    # Verify balance unchanged
    final_balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    assert final_balance == initial_balance, 'Balance changed after unauthorized approve attempt'

def test_reject_leave_success():
    """Test that manager can reject employee's leave request."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('manager1', 'Manager One', 'manager@example.com')
    tracker.add_employee('emp1', 'John Doe', 'john@example.com', manager_id='manager1')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    initial_balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    
    # Manager rejects the request
    tracker.reject(request.request_id, 'manager1')
    
    # Verify status changed to REJECTED
    assert request.status == 'REJECTED', f'Expected status REJECTED, got {request.status}'
    
    # Verify balance unchanged
    final_balance = tracker.get_balance('emp1', LeaveType.CASUAL)
    assert final_balance == initial_balance, f'Balance should remain unchanged, was {initial_balance}, now {final_balance}'

def test_reject_leave_not_authorized():
    """Test that non-manager cannot reject leave request."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType, NotAuthorizedError
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
        NotAuthorizedError = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    assert NotAuthorizedError is not None, 'leave_tracker.models.NotAuthorizedError is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('manager1', 'Manager One', 'manager@example.com')
    tracker.add_employee('emp1', 'John Doe', 'john@example.com', manager_id='manager1')
    tracker.add_employee('emp2', 'Jane Smith', 'jane@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    initial_status = request.status
    
    # Non-manager tries to reject
    with pytest.raises(NotAuthorizedError):
        tracker.reject(request.request_id, 'emp2')
    
    # Verify request status unchanged
    assert request.status == initial_status, 'Request status changed after unauthorized reject attempt'

def test_cancel_leave_success():
    """Test that employee can cancel their own pending request."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    assert request.status == 'PENDING', 'Request should start as PENDING'
    
    # Employee cancels their own request
    tracker.cancel(request.request_id, 'emp1')
    
    # Verify status changed to CANCELLED
    assert request.status == 'CANCELLED', f'Expected status CANCELLED, got {request.status}'

def test_cancel_leave_invalid_state():
    """Test that cancel raises InvalidStateError for non-pending request."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType, InvalidStateError
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
        InvalidStateError = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    assert InvalidStateError is not None, 'leave_tracker.models.InvalidStateError is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('manager1', 'Manager One', 'manager@example.com')
    tracker.add_employee('emp1', 'John Doe', 'john@example.com', manager_id='manager1')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    
    # Approve the request first
    tracker.approve(request.request_id, 'manager1')
    approved_status = request.status
    
    # Try to cancel approved request
    with pytest.raises(InvalidStateError):
        tracker.cancel(request.request_id, 'emp1')
    
    # Verify request status unchanged
    assert request.status == approved_status, 'Request status changed after failed cancel attempt'

def test_cancel_leave_wrong_employee():
    """Test that cancel raises InvalidStateError when called by different employee."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType, InvalidStateError
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
        InvalidStateError = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    assert InvalidStateError is not None, 'leave_tracker.models.InvalidStateError is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    tracker.add_employee('emp2', 'Jane Smith', 'jane@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 10)
    
    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 3)
    
    request = tracker.apply('emp1', LeaveType.CASUAL, start_date, end_date, 'Vacation')
    initial_status = request.status
    
    # Different employee tries to cancel
    with pytest.raises(InvalidStateError):
        tracker.cancel(request.request_id, 'emp2')
    
    # Verify request status unchanged
    assert request.status == initial_status, 'Request status changed after unauthorized cancel attempt'

def test_requests_for_employee():
    """Test that requests_for returns employee's requests in creation order."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('emp1', 'John Doe', 'john@example.com')
    tracker.add_employee('emp2', 'Jane Smith', 'jane@example.com')
    tracker.set_balance('emp1', LeaveType.CASUAL, 20)
    tracker.set_balance('emp2', LeaveType.CASUAL, 20)
    
    # Create requests in specific order
    request1 = tracker.apply('emp1', LeaveType.CASUAL, date(2024, 1, 1), date(2024, 1, 2), 'First')
    request2 = tracker.apply('emp2', LeaveType.CASUAL, date(2024, 1, 3), date(2024, 1, 4), 'Other employee')
    request3 = tracker.apply('emp1', LeaveType.CASUAL, date(2024, 1, 5), date(2024, 1, 6), 'Second')
    request4 = tracker.apply('emp1', LeaveType.CASUAL, date(2024, 1, 7), date(2024, 1, 8), 'Third')
    
    # Get requests for emp1
    emp1_requests = tracker.requests_for('emp1')
    
    assert len(emp1_requests) == 3, f'Expected 3 requests for emp1, got {len(emp1_requests)}'
    
    # Verify order (creation order)
    assert emp1_requests[0].request_id == request1.request_id, 'First request should be request1'
    assert emp1_requests[1].request_id == request3.request_id, 'Second request should be request3'
    assert emp1_requests[2].request_id == request4.request_id, 'Third request should be request4'
    
    # Verify emp2's requests are separate
    emp2_requests = tracker.requests_for('emp2')
    assert len(emp2_requests) == 1, f'Expected 1 request for emp2, got {len(emp2_requests)}'
    assert emp2_requests[0].request_id == request2.request_id, 'emp2 should only have request2'

def test_pending_for_manager():
    """Test that pending_for_manager returns pending requests of manager's team."""
    try:
        from leave_tracker.tracker import LeaveTracker
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveTracker = None
        LeaveType = None
    
    assert LeaveTracker is not None, 'leave_tracker.tracker.LeaveTracker is not implemented yet'
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    tracker = LeaveTracker()
    tracker.add_employee('manager1', 'Manager One', 'manager1@example.com')
    tracker.add_employee('manager2', 'Manager Two', 'manager2@example.com')
    tracker.add_employee('emp1', 'John Doe', 'john@example.com', manager_id='manager1')
    tracker.add_employee('emp2', 'Jane Smith', 'jane@example.com', manager_id='manager1')
    tracker.add_employee('emp3', 'Bob Wilson', 'bob@example.com', manager_id='manager2')
    
    tracker.set_balance('emp1', LeaveType.CASUAL, 20)
    tracker.set_balance('emp2', LeaveType.CASUAL, 20)
    tracker.set_balance('emp3', LeaveType.CASUAL, 20)
    
    # Create various requests
    request1 = tracker.apply('emp1', LeaveType.CASUAL, date(2024, 1, 1), date(2024, 1, 2), 'Pending 1')
    request2 = tracker.apply('emp2', LeaveType.CASUAL, date(2024, 1, 3), date(2024, 1, 4), 'Pending 2')
    request3 = tracker.apply('emp3', LeaveType.CASUAL, date(2024, 1, 5), date(2024, 1, 6), 'Different manager')
    request4 = tracker.apply('emp1', LeaveType.CASUAL, date(2024, 1, 7), date(2024, 1, 8), 'Will be approved')
    
    # Approve one request to make it non-pending
    tracker.approve(request4.request_id, 'manager1')
    
    # Get pending requests for manager1
    manager1_pending = tracker.pending_for_manager('manager1')
    
    # Should include only pending requests from manager1's team
    expected_request_ids = {request1.request_id, request2.request_id}
    actual_request_ids = {req.request_id for req in manager1_pending}
    
    assert actual_request_ids == expected_request_ids, f'Expected requests {expected_request_ids}, got {actual_request_ids}'
    
    # Verify all returned requests are pending
    for req in manager1_pending:
        assert req.status == 'PENDING', f'Request {req.request_id} should be PENDING, got {req.status}'
    
    # Get pending requests for manager2
    manager2_pending = tracker.pending_for_manager('manager2')
    assert len(manager2_pending) == 1, f'Expected 1 pending request for manager2, got {len(manager2_pending)}'
    assert manager2_pending[0].request_id == request3.request_id, 'manager2 should have request3'
