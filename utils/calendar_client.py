import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import config

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarClient:
    """Client for interacting with Google Calendar API"""
    
    def __init__(self, credentials_file=None, token_file=None, calendar_id=None):
        """Initialize with optional custom file paths"""
        self.credentials_file = credentials_file or config.GOOGLE_CREDENTIALS_FILE
        self.token_file = token_file or config.GOOGLE_TOKEN_FILE
        self.calendar_id = calendar_id or config.GOOGLE_CALENDAR_ID
        self.service = self._get_calendar_service()
    
  def _get_calendar_service(self):
    """Authenticate and build the Google Calendar service"""
    creds = None
    
    # If credentials are provided as an environment variable
    google_creds_env = os.environ.get('GOOGLE_CREDENTIALS')
    if google_creds_env:
        # Parse the JSON string from environment variable
        import json
        creds_data = json.loads(google_creds_env)
        client_config = creds_data
        
        # Try to load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_info(
                eval(open(self.token_file, 'r').read()), 
                SCOPES
            )
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(self.token_file, 'w') as token:
            token.write(str(creds.to_json()))
    
    # Build and return the service
    return build('calendar', 'v3', credentials=creds)
    
    def create_event(self, summary, description, start_time, has_time=True, end_time=None):
        """
        Create a Google Calendar event
        
        Args:
            summary: Event title
            description: Event description
            start_time: Start datetime
            has_time: Whether the event has a specific time or is all-day
            end_time: Optional end time (defaults to 1 hour after start for timed events,
                      or same day for all-day events)
        
        Returns:
            The created event object
        """
        event = {
            'summary': summary,
            'description': description,
        }
        
        # Set default end time if not provided
        if not end_time:
            if has_time:
                # Default to 1 hour meeting
                end_time = start_time + datetime.timedelta(hours=1)
            else:
                # All-day event on the same day
                end_time = start_time
        
        # Format event time based on whether it has a specific time or is all-day
        if has_time:
            event['start'] = {'dateTime': start_time.isoformat()}
            event['end'] = {'dateTime': end_time.isoformat()}
        else:
            # Convert to just the date string for all-day events
            date_str = start_time.date().isoformat()
            end_date_str = (end_time.date() + datetime.timedelta(days=1)).isoformat()  # End date is exclusive
            event['start'] = {'date': date_str}
            event['end'] = {'date': end_date_str}
        
        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            return created_event
            
        except Exception as e:
            print(f"Error creating calendar event: {str(e)}")
            return None
    
    def delete_event(self, event_id):
        """Delete a Google Calendar event by ID"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting calendar event: {str(e)}")
            return False
    
    def get_event(self, event_id):
        """Get a Google Calendar event by ID"""
        try:
            return self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
        except Exception as e:
            print(f"Error getting calendar event: {str(e)}")
            return None
