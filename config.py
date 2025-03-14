import os
from dotenv import load_dotenv

load_dotenv()

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-for-testing')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Database configuration
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///sync_data.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Asana API configuration
ASANA_ACCESS_TOKEN = os.getenv('ASANA_ACCESS_TOKEN')
ASANA_WORKSPACE_ID = os.getenv('ASANA_WORKSPACE_ID')

# Google Calendar API configuration
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

# Sync configuration
SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', '15'))
SCHEDULE_TAG_NAME = os.getenv('SCHEDULE_TAG_NAME', 'schedule')
