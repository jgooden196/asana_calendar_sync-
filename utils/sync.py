import datetime
from utils.asana_client import AsanaClient
from utils.calendar_client import GoogleCalendarClient
from utils.db import get_synced_task_by_asana_id, add_synced_task, delete_synced_task
import config

class TaskSynchronizer:
    """Handles the synchronization between Asana tasks and Google Calendar events"""
    
    def __init__(self, asana_client=None, calendar_client=None):
        """Initialize with optional custom clients"""
        self.asana_client = asana_client or AsanaClient()
        self.calendar_client = calendar_client or GoogleCalendarClient()
        self.tag_name = config.SCHEDULE_TAG_NAME
    
    def sync_tasks(self):
        """
        Find tasks with the 'schedule' tag and due date, and create
        corresponding events in Google Calendar
        
        Returns:
            dict: Statistics about the sync operation
        """
        stats = {
            'tasks_found': 0,
            'events_created': 0,
            'already_synced': 0,
            'errors': 0
        }
        
        # Get all non-completed tasks with the schedule tag
        tasks = self.asana_client.get_tasks_with_tag(self.tag_name, completed=False)
        stats['tasks_found'] = len(tasks)
        
        for task in tasks:
            task_id = task['gid']
            task_name = task['name']
            
            # Skip if already synced
            if get_synced_task_by_asana_id(task_id):
                stats['already_synced'] += 1
                continue
            
            # Extract due date
            due_date = self.asana_client.parse_due_date(task)
            
            # Skip if no due date
            if not due_date:
                continue
            
            # Check if the task has a time component
            has_time = self.asana_client.has_time_component(task)
            
            try:
                # Create Google Calendar event
                event = self.calendar_client.create_event(
                    summary=task_name,
                    description=f"Asana task: {task_id}",
                    start_time=due_date,
                    has_time=has_time
                )
                
                if event:
                    # Record the sync in database
                    add_synced_task(
                        asana_task_id=task_id,
                        asana_task_name=task_name,
                        asana_due_date=due_date,
                        google_event_id=event['id']
                    )
                    stats['events_created'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                print(f"Error syncing task {task_id}: {str(e)}")
                stats['errors'] += 1
        
        return stats
