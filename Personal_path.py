import pandas as pd
import requests
import time
import gspread
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

path = r'C:\SEOBUK_Python\#01_Vehicle Searching System'
google_api_auth_file = r'{0}\seobuk-project-server-3a15c50b9073.json'.format(path)
file_name = 'SEOBUK PROJECTION'
sheet_original = 'NUEVO PROJECTION#2'

# Retry 설정
retry_strategy = Retry(
    total=3,
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    status_forcelist=[429, 500, 502, 503, 504],
)

# SSL 인증서 검증 무시 설정
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
session.verify = False

gc = gspread.service_account(filename=google_api_auth_file).open(file_name).worksheet(sheet_original)

def Google_API():
    return google_api_auth_file

def User():
    User = "이규성"
    return User

def File_name():
    return file_name

def Sheet_name():
    return sheet_original

def Read_gspread():
    df_gspread = pd.DataFrame(gc.get_all_records())
    time.sleep(0.1)
    return df_gspread