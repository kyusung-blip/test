import pandas as pd
import requests
import time
import gspread
import os
import json
from google.oauth2.service_account import Credentials
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Environment Variables에서 Google 설정 가져오기 ---
# Enhanced security through environment variables instead of hardcoding credentials
spreadsheet_name = os.getenv("SPREADSHEET_NAME", "SEOBUK PROJECTION")  # Google Sheets 파일 이름
worksheet_name = os.getenv("WORKSHEET_NAME", "NUEVO PROJECTION#2")  # 워크시트 이름

# --- Google Sheets 연결 (지연 초기화를 위해 함수로 캡슐화) ---
def _get_client():
    """내부용: 인증된 gspread 클라이언트를 가져옵니다."""
    try:
        service_account_info = json.loads(os.getenv("GCP_SERVICE_KEY"))
        credentials = Credentials.from_service_account_info(service_account_info)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        raise Exception(f"Google Sheets 클라이언트 생성 실패: {e}")

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
def get_gspread_client_for_personal():
    """
    Personal_path.py에서 사용하는 인증된 gspread 클라이언트를 반환합니다.
    환경 변수 GCP_SERVICE_KEY를 사용하여 인증합니다.
    
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
