from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SyncedTask(db.Model):
    """Model to track synced tasks between Asana and Google Calendar"""
    id = db.Column(db.Integer, primary_key=True)
    asana_task_id = db.Column(db.String(50), unique=True, nullable=False)
    asana_task_name = db.Column(db.String(200), nullable=False)
    asana_due_date = db.Column(db.DateTime, nullable=False)
    google_event_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SyncedTask {self.asana_task_name}>'

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
def get_synced_task_by_asana_id(asana_task_id):
    """Retrieve a synced task by Asana task ID"""
    return SyncedTask.query.filter_by(asana_task_id=asana_task_id).first()

def get_all_synced_tasks():
    """Get all synced tasks"""
    return SyncedTask.query.all()

def add_synced_task(asana_task_id, asana_task_name, asana_due_date, google_event_id):
    """Add a new synced task record"""
    task = SyncedTask(
        asana_task_id=asana_task_id,
        asana_task_name=asana_task_name,
        asana_due_date=asana_due_date,
        google_event_id=google_event_id
    )
    db.session.add(task)
    db.session.commit()
    return task

def delete_synced_task(asana_task_id):
    """Delete a synced task record by Asana task ID"""
    task = get_synced_task_by_asana_id(asana_task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return True
    return False
