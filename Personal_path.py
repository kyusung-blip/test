import pandas as pd
import requests
import time
import gspread
from google.oauth2.service_account import Credentials
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

# Google Sheets 및 API 설정 (Streamlit Secrets 사용)
file_name = st.secrets["gcp_service_account"]["spreadsheet_name"]  # secrets.toml에 추가된 스프레드시트 이름
sheet_original = st.secrets["gcp_service_account"]["worksheet_name"]

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

# gspread를 사용한 인증 및 워크시트 연결 (Streamlit에 저장된 Secret 정보 사용)
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"])
gc = gspread.authorize(credentials)
worksheet = gc.open(file_name).worksheet(sheet_original)

# 공통 함수들
def Google_API():
    """
    Google API 인증 정보를 반환합니다.
    """
    return st.secrets["gcp_service_account"]

def User():
    """
    사용자 이름을 반환합니다.
    """
    user = "이규성"  # 고정된 사용자 이름
    return user

def File_name():
    """
    Google Sheets 파일 이름을 반환합니다.
    """
    return file_name

def Sheet_name():
    """
    Google Sheets 워크시트 이름을 반환합니다.
    """
    return sheet_original

def Read_gspread():
    """
    Google Sheets 데이터를 읽어 pandas DataFrame으로 반환합니다.
    """
    df_gspread = pd.DataFrame(worksheet.get_all_records())
    time.sleep(0.1)
    return df_gspread
