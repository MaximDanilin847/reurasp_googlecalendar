from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError 
from google.oauth2 import service_account
import os
from setup.constants import *

# Настраиваем аутентификацию Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Authenticate and create a service for Google Calendar."""
    creds = None
    
    # load from service account file
    if os.path.exists('setup/servicekey.json'):
        try:
            creds = service_account.Credentials.from_service_account_file('setup/servicekey.json')
            print("Authenticated using service account")
        except Exception as e:
            print(f"Error loading service account credentials: {e}")
    
    # load from token.json (authorized user file)
    if not creds and os.path.exists('setup/token.json'):
        try:
            creds = Credentials.from_authorized_user_file('setup/token.json', SCOPES)
            print("Authenticated using saved user credentials")
        except Exception as e:
            print(f"Error loading saved credentials: {e}")
    
    # authenticate with client_secrets_file
    if not creds and os.path.exists('setup/credentials.json'):
        try:
            flow = InstalledAppFlow.from_client_secrets_file('setup/credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            
            # Save the credentials for the next run
            with open('setup/token.json', 'w') as token:
                token.write(creds.to_json())
            print("Authenticated using client secrets and saved credentials")
        except Exception as e:
            print(f"Error authenticating with client secrets: {e}")
    
    if not creds:
        raise Exception("Failed to obtain valid credentials")
        
    return build('calendar', 'v3', credentials=creds)
    
def create_google_calendar_event(service, summary, start_time, end_time, description):
    """Создание события в Google Calendar."""
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Europe/Moscow',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Europe/Moscow',
        },
    }
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created_event
def event_exists(service, calendar_id, subject, start_time, end_time):
    try:
    # Ищем события на определенный временной промежуток
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            q=subject  # Ищем по названию предмета
        ).execute()
        
        events = events_result.get('items', [])
        
        # Проверяем, есть ли события с таким же названием
        for event in events:
            if event['summary'] == subject:
                return True
        return False
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False
