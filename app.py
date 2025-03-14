from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import json
from datetime import datetime

import config
from utils.db import init_db, get_all_synced_tasks
from utils.sync import TaskSynchronizer
from utils.asana_client import AsanaClient
from utils.calendar_client import GoogleCalendarClient

app = Flask(__name__)
app.config.from_object(config)

# Initialize database
init_db(app)

@app.route('/')
def index():
    """Render the dashboard page"""
    synced_tasks = get_all_synced_tasks()
    return render_template('dashboard.html', synced_tasks=synced_tasks)

@app.route('/api/sync', methods=['POST'])
def sync_tasks():
    """API endpoint to trigger task synchronization"""
    synchronizer = TaskSynchronizer()
    stats = synchronizer.sync_tasks()
    
    return jsonify({
        'success': True,
        'stats': stats,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/auth/google', methods=['GET'])
def google_auth():
    """Route to handle Google OAuth callback"""
    # Just initialize the client which will handle the auth flow if needed
    client = GoogleCalendarClient()
    return redirect(url_for('index'))

@app.route('/api/status', methods=['GET'])
def status():
    """API endpoint to check authentication and connection status"""
    status_info = {
        'asana': False,
        'google_calendar': False
    }
    
    # Check Asana connection
    try:
        client = AsanaClient()
        # Try to make a simple API call
        client._make_request("GET", "users/me")
        status_info['asana'] = True
    except Exception:
        pass
    
    # Check Google Calendar connection
    try:
        client = GoogleCalendarClient()
        # If we can initialize the service, connection is working
        if client.service:
            status_info['google_calendar'] = True
    except Exception:
        pass
    
    return jsonify(status_info)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
