import time
import os

from setup.constants import calendar_id, pair_times
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def authenticate_google_calendar():
    """Authenticate and create a service for Google Calendar."""
    creds = None
    if os.path.exists('setup/token.json'):
        creds = Credentials.from_authorized_user_file('setup/token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('setup/credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('setup/token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

# Настраиваем аутентификацию Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Authenticate and create a service for Google Calendar."""
    creds = None
    if os.path.exists('setup/token.json'):
        creds = Credentials.from_authorized_user_file('setup/token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('setup/credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('setup/token.json', 'w') as token:
            token.write(creds.to_json())
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

# Настраиваем опции для Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Запускаем браузер в фоновом режиме

# Инициализируем веб-драйвер
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# URL с расписанием
url = 'https://rasp.rea.ru/?q=15.27%D0%B4-%D0%BF%D0%B805%2F24%D0%BC'

# Открываем страницу в браузере
driver.get(url)

# Ожидаем некоторое время для полной загрузки страницы
time.sleep(5)

# Получаем HTML-код после полной загрузки
html_content = driver.page_source

# Закрываем браузер
driver.quit()

# Используем BeautifulSoup для парсинга страницы
soup = BeautifulSoup(html_content, 'html.parser')

# Аутентификация в Google Calendar
service = authenticate_google_calendar()

# Проверяем наличие блоков расписания
zone_timetable = soup.select_one('div#zoneTimetable')
if zone_timetable:
    print("Блок с расписанием найден")

    # Ищем все div.col-lg-6 внутри zoneTimetable
    schedule_blocks = zone_timetable.select('div.col-lg-6')
    print(f"Найдено {len(schedule_blocks)} блоков с парами")

    for i, block in enumerate(schedule_blocks):
        print(f"Проверяем блок {i + 1}")

        # Проверяем наличие заголовка с датой
        date_header = block.select_one('thead th.dayh h5')
        if date_header:
            date_text = date_header.text.strip()
            print(f"Дата: {date_text}")

            # Преобразуем текст даты в формат day.month.year
            day, month, year = date_text.split(", ")[1].split(".")
        else:
            print(f"Дата не найдена в блоке {i + 1}")
            continue  # Пропускаем, если нет даты

        # Проверяем наличие строк с занятиями
        slots = block.select('tr.slot')
        print(f"Найдено {len(slots)} занятий в блоке {i + 1}")

        for slot in slots:
            # Номер пары
            pair_number_info = slot.select_one('td span.pcap')
            if pair_number_info:
                pair_number = pair_number_info.text.strip().split()[0]  # Извлекаем номер пары
                time_range = pair_times.get(pair_number)  # Получаем время для данной пары
                
                if time_range:
                    start_time, end_time = time_range

                    # Создаем строку времени в формате для Google Calendar (RFC3339)
                    start_datetime = f"{year}-{month}-{day}T{start_time}:00+03:00"
                    end_datetime = f"{year}-{month}-{day}T{end_time}:00+03:00"
                    print(f"Занятие {pair_number}: {start_time} - {end_time} ({start_datetime} - {end_datetime})")

                    # Название предмета и описание
                    description = slot.select_one('td a.task')
                    if description:
                        # Получаем текст занятия и разбиваем его по пустым строкам
                        full_text = description.get_text(separator="\n").strip()
                        
                        # Разбиваем по пустым строкам (двойной перевод строки или два подряд символа новой строки)
                        parts = full_text.split("\n\n")
                        
                        # Название предмета — это первый элемент
                        subject = parts[0].strip()
                        
                        # Описание — это все остальное
                        description_text = parts[1:] if len(parts) > 1 else ["Без описания"]

                        print(f"Занятие: {subject}")
                        print(f"Описание: {description_text}")

                        if not event_exists(service, calendar_id, subject, start_datetime, end_datetime):
                            # Если события с таким названием и временем нет, создаем новое событие
                            event = {
                                'summary': subject,
                                'description': description_text,
                                'start': {
                                    'dateTime': start_datetime,
                                    'timeZone': 'Europe/Moscow',
                                },
                                'end': {
                                    'dateTime': end_datetime,
                                    'timeZone': 'Europe/Moscow',
                                },
                            }

                            # Создаем событие
                            created_event = create_google_calendar_event(
                            service,
                            subject,
                            start_datetime,
                            end_datetime,
                            description_text
                        )
                            print(f"Создано событие: {created_event['htmlLink']}")
                        else:
                            print(f"Событие '{subject}' на это время уже существует.")
                    else:
                        print("Занятие не найдено")
                else:
                    print(f"Время для пары {pair_number} не найдено в словаре.")
            else:
                print("Номер пары не найден")
else:
    print("Блок с расписанием НЕ найден")
