import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from utils.calendar_client import GoogleCalendarClient

@pytest.fixture
def mock_google_apis():
    """Fixture to mock Google API libraries"""
    with patch('utils.calendar_client.Credentials') as mock_creds, \
         patch('utils.calendar_client.InstalledAppFlow') as mock_flow, \
         patch('utils.calendar_client.Request') as mock_request, \
         patch('utils.calendar_client.build') as mock_build:
        
        # Configure the mock service
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service
        
        yield {
            'creds': mock_creds,
            'flow': mock_flow,
            'request': mock_request,
            'build': mock_build,
            'service': mock_service,
            'events': mock_events
        }

@pytest.fixture
def calendar_client(mock_google_apis, monkeypatch):
    """Create a Calendar client with mocked dependencies"""
    # Mock file operations
    monkeypatch.setattr('os.path.exists', lambda path: True)
    monkeypatch.setattr('builtins.open', MagicMock())
    
    return GoogleCalendarClient(
        credentials_file="mock_creds.json",
        token_file="mock_token.json",
        calendar_id="mock_calendar"
    )

def test_init(calendar_client):
    """Test client initialization"""
    assert calendar_client.credentials_file == "mock_creds.json"
    assert calendar_client.token_file == "mock_token.json"
    assert calendar_client.calendar_id == "mock_calendar"
    assert calendar_client.service is not None

def test_get_calendar_service(mock_google_apis, monkeypatch):
    """Test authentication and service creation"""
    # Mock file reading
    monkeypatch.setattr('os.path.exists', lambda path: True)
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = "{'token': 'mock_token'}"
    monkeypatch.setattr('builtins.open', lambda path, mode: mock_file)
    
    # Mock credentials validation
    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_google_apis['creds'].from_authorized_user_info.return_value = mock_creds_instance
    
    client = GoogleCalendarClient(
        credentials_file="mock_creds.json",
        token_file="mock_token.json"
    )
    
    # Check the service was built correctly
    mock_google_apis['build'].assert_called_once_with(
        'calendar', 'v3', credentials=mock_creds_instance
    )

def test_create_event_with_time(calendar_client, mock_google_apis):
    """Test creating an event with a specific time"""
    # Mock event creation response
    mock_insert = MagicMock()
    mock_google_apis['events'].insert.return_value = mock_insert
    mock_insert.execute.return_value = {"id": "event123"}
    
    # Create a timed event
    start_time = datetime.now()
    event = calendar_client.create_event(
        summary="Test Event",
        description="Test Description",
        start_time=start_time,
        has_time=True
    )
    
    # Check the event was created correctly
    mock_google_apis['events'].insert.assert_called_once()
    # Get the call arguments
    args, kwargs = mock_google_apis['events'].insert.call_args
    
    # Check calendar ID
    assert kwargs['calendarId'] == "mock_calendar"
    
    # Check event data
    event_body = kwargs['body']
    assert event_body['summary'] == "Test Event"
    assert event_body['description'] == "Test Description"
    assert 'dateTime' in event_body['start']
    assert 'dateTime' in event_body['end']

def test_create_all_day_event(calendar_client, mock_google_apis):
    """Test creating an all-day event"""
    # Mock event creation response
    mock_insert = MagicMock()
    mock_google_apis['events'].insert.return_value = mock_insert
    mock_insert.execute.return_value = {"id": "event123"}
    
    # Create an all-day event
    start_time = datetime.now()
    event = calendar_client.create_event(
        summary="Test All-Day Event",
        description="Test Description",
        start_time=start_time,
        has_time=False
    )
    
    # Check the event was created correctly
    args, kwargs = mock_google_apis['events'].insert.call_args
    
    # Check event data
    event_body = kwargs['body']
    assert 'date' in event_body['start']
    assert 'date' in event_body['end']
    # End date should be the next day for all-day events
    assert event_body['end']['date'] != event_body['start']['date']

def test_delete_event(calendar_client, mock_google_apis):
    """Test deleting an event"""
    # Mock delete response
    mock_delete = MagicMock()
    mock_google_apis['events'].delete.return_value = mock_delete
    
    # Delete an event
    result = calendar_client.delete_event("event123")
    
    # Check the delete request was made correctly
    mock_google_apis['events'].delete.assert_called_once_with(
        calendarId="mock_calendar",
        eventId="event123"
    )
    assert result is True
