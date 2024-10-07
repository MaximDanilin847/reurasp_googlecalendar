# reurasp_googlecalendar
Google Calendar Integration with REU Rasp

All setup files, including token and credentials, are need to placed in 'setup' folder. You can get token and credentials by using Google Cloud Console. 

Calendar id, pair times, base and group URL are placed inside 'setup/constants.py'

Google Calendar API is written inside 'googlecalendarAPI.py'

# TODO
- Add option to load next weeks
- Get teacher name via click

# FIRST LAUNCH
To run, you should install all the libraries used:
pip install webdriver_manager
pip install selenium
pip install bs4
pip install google
pip install google_auth_oauthlib
pip install google-api-python-client