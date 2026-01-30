import pandas as pd
import requests
import time
import gspread
from google.oauth2.service_account import Credentials
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

# --- Streamlit Secrets에서 Google 인증 정보 가져오기 ---
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
spreadsheet_name = st.secrets["gcp_service_account"]["spreadsheet_name"]  # Google Sheets 파일 이름
worksheet_name = st.secrets["gcp_service_account"]["worksheet_name"]  # 워크시트 이름

# --- Google Sheets 연결 ---
gc = gspread.authorize(credentials)  # 인증 및 클라이언트 초기화
worksheet = gc.open(spreadsheet_name).worksheet(worksheet_name)  # 특정 Google Sheets의 워크시트 열기

# --- Retry 설정 ---
retry_strategy = Retry(
    total=3,
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 상태 코드
)
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
session.verify = False  # SSL 인증서 검증 무시 (필요 시 활성화 가능)

# --- 함수 정의 ---
def Google_API():
    """
    Streamlit Secrets에서 읽어온 인증 정보를 반환합니다.
    """
    return st.secrets["gcp_service_account"]

def User():
    """
    사용자 이름을 반환합니다. (고정 값)
    """
    return "이규성"

def File_name():
    """
    Google 스프레드시트 이름을 반환합니다.
    """
    return spreadsheet_name

def Sheet_name():
    """
    Google 워크시트 이름을 반환합니다.
    """
    return worksheet_name

def Read_gspread():
    """
    Google Sheets 데이터를 읽어서 pandas DataFrame으로 변환합니다.
    """
    df_gspread = pd.DataFrame(worksheet.get_all_records())  # Google 워크시트 데이터를 읽기
    time.sleep(0.1)
    return df_gspread
