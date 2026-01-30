import pandas as pd
import requests
import time
import gspread
from auth import get_credentials, get_gspread_client
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

# --- Streamlit Secrets에서 Google 인증 정보 가져오기 ---
credentials = get_credentials("gcp_service_account")
spreadsheet_name = st.secrets["gcp_service_account"]["spreadsheet_name"]  # Google Sheets 파일 이름
worksheet_name = st.secrets["gcp_service_account"]["worksheet_name"]  # 워크시트 이름

# --- Google Sheets 연결 ---
gc = get_gspread_client("gcp_service_account")  # 인증 및 클라이언트 초기화
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
    DEPRECATED: 이 함수는 더 이상 사용하지 않습니다.
    대신 get_gspread_client_for_seobuk()를 사용하세요.
    
    이전에는 Streamlit Secrets를 반환했으나, 이는 gspread.service_account(filename=...)와
    호환되지 않습니다. 대신 인증된 클라이언트를 직접 사용하세요.
    """
    raise DeprecationWarning(
        "Google_API() is deprecated. Use get_gspread_client_for_seobuk() instead."
    )

def get_gspread_client_for_seobuk():
    """
    seobuk 프로젝트용 인증된 gspread 클라이언트를 반환합니다.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트
    """
    return gc

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
