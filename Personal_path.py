import pandas as pd
import requests
import time
import gspread
from auth import get_gspread_client
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

# --- Streamlit Secrets에서 Google 설정 가져오기 ---
# Note: Personal_path.py uses the generic "gcp_service_account" key
spreadsheet_name = st.secrets["gcp_service_account"]["spreadsheet_name"]  # Google Sheets 파일 이름
worksheet_name = st.secrets["gcp_service_account"]["worksheet_name"]  # 워크시트 이름

# --- Google Sheets 연결 (지연 초기화를 위해 함수로 캡슐화) ---
def _get_client():
    """내부용: 인증된 gspread 클라이언트를 가져옵니다 (캐시됨)."""
    return get_gspread_client("gcp_service_account")

def _get_worksheet():
    """내부용: 워크시트 객체를 가져옵니다."""
    return _get_client().open(spreadsheet_name).worksheet(worksheet_name)

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
    대신 get_gspread_client_for_personal()를 사용하세요.
    
    이전에는 Streamlit Secrets를 반환했으나, 이는 gspread.service_account(filename=...)와
    호환되지 않습니다. 대신 인증된 클라이언트를 직접 사용하세요.
    """
    raise NotImplementedError(
        "Google_API() is deprecated and has been removed. "
        "Use get_gspread_client_for_personal() instead."
    )

def get_gspread_client_for_personal():
    """
    Personal_path.py에서 사용하는 인증된 gspread 클라이언트를 반환합니다.
    이 함수는 "gcp_service_account" 키를 사용합니다.
    
    Note: 캐싱은 내부 auth.get_gspread_client()에서 처리됩니다.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트
    """
    return _get_client()

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
    worksheet = _get_worksheet()
    df_gspread = pd.DataFrame(worksheet.get_all_records())  # Google 워크시트 데이터를 읽기
    time.sleep(0.1)
    return df_gspread
