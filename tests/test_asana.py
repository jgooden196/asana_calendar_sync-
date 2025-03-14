import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from utils.asana_client import AsanaClient

@pytest.fixture
def mock_requests():
    """Fixture to mock requests module"""
    with patch('utils.asana_client.requests') as mock_requests:
        yield mock_requests

@pytest.fixture
def asana_client():
    """Create an Asana client with mock credentials"""
    return AsanaClient(
        access_token="test_token",
        workspace_id="test_workspace"
    )

def test_init(asana_client):
    """Test client initialization"""
    assert asana_client.access_token == "test_token"
    assert asana_client.workspace_id == "test_workspace"
    assert asana_client.headers["Authorization"] == "Bearer test_token"

def test_make_request(asana_client, mock_requests):
    """Test the _make_request method"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "test_data"}
    mock_response.raise_for_status.return_value = None
    mock_requests.request.return_value = mock_response
    
    # Make the request
    result = asana_client._make_request("GET", "test_endpoint", {"param": "value"})
    
    # Check the request was made correctly
    mock_requests.request.assert_called_once_with(
        method="GET",
        url="https://app.asana.com/api/1.0/test_endpoint",
        headers=asana_client.headers,
        params={"param": "value"},
        json=None
    )
    
    # Check the result
    assert result == {"data": "test_data"}

def test_get_tasks_with_tag(asana_client, mock_requests):
    """Test getting tasks with a specific tag"""
    # Mock tag response
    tag_response = MagicMock()
    tag_response.json.return_value = {
        "data": [
            {"gid": "tag1", "name": "other_tag"},
            {"gid": "tag2", "name": "schedule"}
        ]
    }
    
    # Mock tasks response
    tasks_response = MagicMock()
    tasks_response.json.return_value = {
        "data": [
            {"gid": "task1", "name": "Test Task 1", "due_on": "2023-10-10"},
            {"gid": "task2", "name": "Test Task 2", "due_at": "2023-10-10T15:00:00Z"}
        ]
    }
    
    # Setup request side effect
    mock_requests.request.side_effect = [tag_response, tasks_response]
    
    # Call the method
    tasks = asana_client.get_tasks_with_tag("schedule")
    
    # Check the result
    assert len(tasks) == 2
    assert tasks[0]["gid"] == "task1"
    assert tasks[1]["gid"] == "task2"
    
    # Check the requests were made correctly
    assert mock_requests.request.call_count == 2
    # First call should be to get the tag
    mock_requests.request.assert_any_call(
        method="GET",
        url="https://app.asana.com/api/1.0/workspaces/test_workspace/tags",
        headers=asana_client.headers,
        params={"limit": 100},
        json=None
    )
    # Second call should be to get the tasks with that tag
    mock_requests.request.assert_any_call(
        method="GET",
        url="https://app.asana.com/api/1.0/tags/tag2/tasks",
        headers=asana_client.headers,
        params={"opt_fields": "name,due_on,due_at,completed", "completed": False},
        json=None
    )

def test_parse_due_date(asana_client):
    """Test parsing due dates from Asana tasks"""
    # Test with due_at (includes time)
    task1 = {"due_at": "2023-10-10T15:00:00Z"}
    date1 = asana_client.parse_due_date(task1)
    assert date1.year == 2023
    assert date1.month == 10
    assert date1.day == 10
    assert date1.hour == 15
    assert date1.minute == 0
    
    # Test with only due_on (date only)
    task2 = {"due_on": "2023-10-10"}
    date2 = asana_client.parse_due_date(task2)
    assert date2.year == 2023
    assert date2.month == 10
    assert date2.day == 10
    assert date2.hour == 0
    assert date2.minute == 0
    
    # Test with no due date
    task3 = {}
    date3 = asana_client.parse_due_date(task3)
    assert date3 is None

def test_has_time_component(asana_client):
    """Test checking if a task has a time component"""
    # Task with due_at should return True
    task1 = {"due_at": "2023-10-10T15:00:00Z"}
    assert asana_client.has_time_component(task1) is True
    
    # Task with due_on only should return False
    task2 = {"due_on": "2023-10-10"}
    assert asana_client.has_time_component(task2) is False
    
    # Task with no due date should return False
    task3 = {}
    assert asana_client.has_time_component(task3) is False
