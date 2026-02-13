import pandas as pd
import requests
import time
import gspread
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from oauth2client.service_account import ServiceAccountCredentials

# 현재 파일의 위치를 기준으로 json 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 깃허브 제일 바깥에 있다고 하신 json 파일명으로 설정
JSON_FILE_NAME = "concise-isotope-456307-n5-8cf3eb97b093.json" 
JSON_PATH = os.path.join(BASE_DIR, JSON_FILE_NAME)

def get_spreadsheet_open(name):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # 절대 경로 대신 자동 계산된 JSON_PATH 사용
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_PATH, scope)
    gc = gspread.authorize(creds)
    return gc.open(name)

def get_nuevo_projection_sheet():
    # 말씀하신 'SEOBUK PROJECTION' 파일의 'NUEVO PROJECTION#2' 시트 호출
    return get_spreadsheet_open("SEOBUK PROJECTION").worksheet("NUEVO PROJECTION#2")

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

