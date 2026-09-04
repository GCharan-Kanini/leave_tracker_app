import pytest

def test_leave_type_enum_members():
    """Test that LeaveType enum exists with required members CASUAL, SICK, VACATION."""
    try:
        from leave_tracker.models import LeaveType
    except (ImportError, AttributeError):
        LeaveType = None
    
    assert LeaveType is not None, 'leave_tracker.models.LeaveType is not implemented yet'
    
    # Verify enum has exactly the required members
    assert hasattr(LeaveType, 'CASUAL'), 'LeaveType.CASUAL member is missing'
    assert hasattr(LeaveType, 'SICK'), 'LeaveType.SICK member is missing'
    assert hasattr(LeaveType, 'VACATION'), 'LeaveType.VACATION member is missing'
    
    # Verify these are the only members (no extras)
    expected_members = {'CASUAL', 'SICK', 'VACATION'}
    actual_members = {member.name for member in LeaveType}
    assert actual_members == expected_members, f'LeaveType has unexpected members: {actual_members - expected_members}'
