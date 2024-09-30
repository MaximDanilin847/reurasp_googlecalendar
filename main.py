import time

from setup.constants import *
from bs4 import BeautifulSoup


from selenium import webdriver

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from googlecalendarAPI import *

# Настраиваем опции для Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Запускаем браузер в фоновом режиме

# Инициализdируем веб-драйвер
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# URL с расписанием
url = base_url + group

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
                        description_text = "\n".join(parts[1:]).strip() if len(parts) > 1 else "Без описания"

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
