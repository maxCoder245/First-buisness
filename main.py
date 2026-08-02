import os
import datetime
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account.json'

# Configuration
CALENDAR_ID = 'your_email@gmail.com' 
TIMEZONE = 'Australia/Sydney' 

def get_calendar_service():
    """Authenticates and returns the Calendar API service."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return None
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

def check_availability(service, target_date, target_time, duration_minutes=30):
    """
    Uses the FreeBusy API to check if the target time slot is open.
    target_date format: 'YYYY-MM-DD'
    target_time format: 'HH:MM'
    """
    # Create timezone-aware datetime objects
    start_dt = datetime.datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
    start_dt = start_dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "timeZone": TIMEZONE,
        "items": [{"id": CALENDAR_ID}]
    }
    
    try:
        events_result = service.freebusy().query(body=body).execute()
        calendars = events_result.get('calendars', {})
        busy_slots = calendars.get(CALENDAR_ID, {}).get('busy', [])
        
        # If the busy array is empty, the slot is available
        return len(busy_slots) == 0
    except HttpError as error:
        print(f"Error checking calendar: {error}")
        return False

def create_booking_event(service, target_date, target_time, duration_minutes, booking_details):
    """
    Creates a new calendar event for the confirmed booking.
    """
    start_dt = datetime.datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
    start_dt = start_dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
    
    event = {
        'summary': f"Service Booking: {booking_details['service']}",
        'location': booking_details['address'],
        'description': f"Service: {booking_details['service']}\nExpected Revenue: ${booking_details['cost']}",
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': TIMEZONE,
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': TIMEZONE,
        },
        # Color coding makes it easy to spot on your personal calendar (e.g., 9 = Blueberry/Blue)
        'colorId': '9' 
    }
    
    try:
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return created_event.get('htmlLink')
    except HttpError as error:
        print(f"Error creating event: {error}")
        return None
