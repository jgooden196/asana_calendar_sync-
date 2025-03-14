import requests
from datetime import datetime, timezone
import config

class AsanaClient:
    """Client for interacting with Asana API"""
    
    BASE_URL = "https://app.asana.com/api/1.0"
    
    def __init__(self, access_token=None, workspace_id=None):
        """Initialize with optional custom credentials"""
        self.access_token = access_token or config.ASANA_ACCESS_TOKEN
        self.workspace_id = workspace_id or config.ASANA_WORKSPACE_ID
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
    def _make_request(self, method, endpoint, params=None, data=None):
        """Make an HTTP request to the Asana API"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            json=data
        )
        
        # Raise an exception for bad responses
        response.raise_for_status()
        
        return response.json()
    
    def get_tasks_with_tag(self, tag_name, completed=False):
        """Get all tasks with a specific tag"""
        try:
            # First, get the tag ID
            tag_data = self._make_request(
                "GET", 
                f"workspaces/{self.workspace_id}/tags",
                params={"limit": 100}
            )
            
            tag_id = None
            for tag in tag_data.get("data", []):
                if tag["name"].lower() == tag_name.lower():
                    tag_id = tag["gid"]
                    break
            
            if not tag_id:
                return []
            
            # Now, get tasks with this tag
            tasks_data = self._make_request(
                "GET",
                f"tags/{tag_id}/tasks",
                params={
                    "opt_fields": "name,due_on,due_at,completed",
                    "completed": completed
                }
            )
            
            return tasks_data.get("data", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tasks with tag {tag_name}: {str(e)}")
            return []
    
    def parse_due_date(self, task):
        """Parse the due date from an Asana task"""
        # First check if due_at exists (includes time)
        if task.get("due_at"):
            return datetime.fromisoformat(task["due_at"].replace("Z", "+00:00"))
        
        # If only due_on exists (date only)
        elif task.get("due_on"):
            # Return a datetime for the start of the day
            date_str = task["due_on"]
            return datetime.fromisoformat(f"{date_str}T00:00:00+00:00")
        
        return None
    
    def has_time_component(self, task):
        """Check if the task has a time component in its due date"""
        return "due_at" in task and task["due_at"] is not None
    
    def add_tag_to_task(self, task_id, tag_name):
        """Add a tag to a task"""
        try:
            # First, ensure the tag exists
            tag_data = self._make_request(
                "GET", 
                f"workspaces/{self.workspace_id}/tags",
                params={"limit": 100}
            )
            
            tag_id = None
            for tag in tag_data.get("data", []):
                if tag["name"].lower() == tag_name.lower():
                    tag_id = tag["gid"]
                    break
            
            # If tag doesn't exist, create it
            if not tag_id:
                create_tag_response = self._make_request(
                    "POST",
                    "tags",
                    data={
                        "data": {
                            "name": tag_name,
                            "workspace": self.workspace_id
                        }
                    }
                )
                tag_id = create_tag_response["data"]["gid"]
            
            # Add the tag to the task
            response = self._make_request(
                "POST",
                f"tasks/{task_id}/addTag",
                data={
                    "data": {
                        "tag": tag_id
                    }
                }
            )
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error adding tag to task {task_id}: {str(e)}")
            return False
