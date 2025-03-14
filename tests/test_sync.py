import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from utils.sync import TaskSynchronizer

@pytest.fixture
def mock_asana_client():
    """Create a mock Asana client"""
    client = MagicMock()
    client.tag_name = "schedule"
    return client

@pytest.fixture
def mock_calendar_client():
    """Create a mock Google Calendar client"""
    client = MagicMock()
    return client

@pytest.fixture
def sync_mock_db():
    """Mock database functions"""
    with patch('utils.sync.get_synced_task_by_asana_id') as mock_get, \
         patch('utils.sync.add_synced_task') as mock_add:
        mock_get.return_value = None  # Default: task not synced yet
        yield {
            'get': mock_get,
            'add': mock_add
        }

@pytest.fixture
def synchronizer(mock_asana_client, mock_calendar_client):
    """Create a TaskSynchronizer with mock clients"""
    return TaskSynchronizer(
        asana_client=mock_asana_client,
        calendar_client=mock_calendar_client
    )

def test_sync_tasks_no_tasks(synchronizer, mock_asana_client):
    """Test syncing when no tasks are found"""
    # Configure mock to return no tasks
    mock_asana_client.get_tasks_with_tag.return_value = []
    
    # Run sync
    stats = synchronizer.sync_tasks()
    
    # Check results
    assert stats['tasks_found'] == 0
    assert stats['events_created'] == 0
    
    # Verify method calls
    mock_asana_client.get_tasks_with_tag.assert_called_once_with("schedule", completed=False)

def test_sync_tasks_already_synced(synchronizer, mock_asana_client, sync_mock_db):
    """Test syncing a task that's already been synced"""
    # Mock a task that was already synced
    mock_asana_client.get_tasks_with_tag.return_value = [
        {"gid": "task1", "name": "Test Task", "due_on": "2023-10-10"}
    ]
    
    # Mock that this task is already in the database
    sync_mock_db['get'].return_value = {"id": 1}
    
    # Run sync
    stats = synchronizer.sync_tasks()
    
    # Check results
    assert stats['tasks_found'] == 1
    assert stats['already_synced'] == 1
    assert stats['events_created'] == 0
    
    # Verify method calls
    sync_mock_db['get'].assert_called_once_with("task1")
    
    # Calendar client should not be called
    synchronizer.calendar_client.create_event.assert_not_called()

def test_sync_tasks_new_task(synchronizer, mock_asana_client, mock_calendar_client, sync_mock_db):
    """Test syncing a new task that hasn't been synced yet"""
    # Mock a task with a due date
    mock_task = {"gid": "task1", "name": "Test Task", "due_on": "2023-10-10"}
    mock_asana_client.get_tasks_with_tag.return_value = [mock_task]
    
    # Mock due date parsing
    due_date = datetime(2023, 10, 10)
    mock_asana_client.parse_due_date.return_value = due_date
    
    # Mock time component check (all-day event)
    mock_asana_client.has_time_component.return_value = False
    
    # Mock calendar event creation
    mock_event = {"id": "event123"}
    mock_calendar_client.create_event.return_value = mock_event
    
    # Run sync
    stats = synchronizer.sync_tasks()
    
    # Check results
    assert stats['tasks_found'] == 1
    assert stats['already_synced'] == 0
    assert stats['events_created'] == 1
    
    # Verify method calls
    mock_asana_client.parse_due_date.assert_called_once_with(mock_task)
    mock_asana_client.has_time_component.assert_called_once_with(mock_task)
    
    # Verify calendar event creation
    mock_calendar_client.create_event.assert_called_once_with(
        summary="Test Task",
        description="Asana task: task1",
        start_time=due_date,
        has_time=False
    )
    
    # Verify database record creation
    sync_mock_db['add'].assert_called_once_with(
        asana_task_id="task1",
        asana_task_name="Test Task",
        asana_due_date=due_date,
        google_event_id="event123"
    )

def test_sync_tasks_timed_event(synchronizer, mock_asana_client, mock_calendar_client, sync_mock_db):
    """Test syncing a task with a specific time component"""
    # Mock a task with a due date and time
    mock_task = {"gid": "task1", "name": "Test Task", "due_at": "2023-10-10T15:00:00Z"}
    mock_asana_client.get_tasks_with_tag.return_value = [mock_task]
    
    # Mock due date parsing
    due_date = datetime(2023, 10, 10, 15, 0, 0)
    mock_asana_client.parse_due_date.return_value = due_date
    
    # Mock time component check (timed event)
    mock_asana_client.has_time_component.return_value = True
    
    # Mock calendar event creation
    mock_event = {"id": "event123"}
    mock_calendar_client.create_event.return_value = mock_event
    
    # Run sync
    stats = synchronizer.sync_tasks()
    
    # Check results
    assert stats['events_created'] == 1
    
    # Verify calendar event creation with time component
    mock_calendar_client.create_event.assert_called_once_with(
        summary="Test Task",
        description="Asana task: task1",
        start_time=due_date,
        has_time=True
    )

def test_sync_tasks_no_due_date(synchronizer, mock_asana_client, mock_calendar_client):
    """Test syncing a task without a due date"""
    # Mock a task without a due date
    mock_task = {"gid": "task1", "name": "Test Task No Due Date"}
    mock_asana_client.get_tasks_with_tag.return_value = [mock_task]
    
    # Mock due date parsing (no due date)
    mock_asana_client.parse_due_date.return_value = None
    
    # Run sync
    stats = synchronizer.sync_tasks()
    
    # Check results - no events should be created
    assert stats['tasks_found'] == 1
    assert stats['events_created'] == 0
    
    # Calendar client should not be called
    mock_calendar_client.create_event.assert_not_called()

def test_sync_tasks_error_handling(synchronizer, mock_asana_client, mock_calendar_client, sync_mock_db):
    """Test error handling during sync process"""
    # Mock a task with a due date
    mock_task = {"gid": "task1", "name": "Test Task", "due_on": "2023-10-10"}
    mock_asana_client.get_tasks_with_tag.return_value = [mock_task]
    
    # Mock due date parsing
    due_date = datetime(2023, 10, 10)
    mock_asana_client.parse_due_date.return_value = due_date
    
    # Mock calendar event creation to fail
    mock_calendar_client.create_event.side_effect = Exception("API error")
    
    # Run sync
    stats = synchronizer.sync_tasks()
    
    # Check results
    assert stats['tasks_found'] == 1
    assert stats['errors'] == 1
    assert stats['events_created'] == 0
    
    # Database add should not be called
    sync_mock_db['add'].assert_not_called()
