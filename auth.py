import os
import json
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import time

# --- Google Sheets 인증 ---
def connect_to_google_sheets():
    """
    Google Sheets와 연결하여 인증된 Worksheet 객체를 반환합니다.

    Returns:
        worksheet: gspread.Worksheet 객체
    Raises:
        Exception: 인증 실패 시 에러 메시지 출력
    """
    try:
        service_account_info = json.loads(os.getenv("GCP_SERVICE_KEY"))  # JSON 읽기
        credentials = Credentials.from_service_account_info(service_account_info)
        client = gspread.authorize(credentials)
        sheet_name = os.getenv("SPREADSHEET_NAME", "SEOBUK PROJECTION")
        worksheet_name = os.getenv("WORKSHEET_NAME", "NUEVO PROJECTION#2")
        worksheet = client.open(sheet_name).worksheet(worksheet_name)  # 워크시트 열기
        return worksheet
    except Exception as e:
        raise Exception(f"Google Sheets 연결 실패: {e}")

# --- Google Sheets 데이터 읽기 ---
def read_google_sheets():
    """
    pandas DataFrame으로 Google Sheets 데이터를 반환합니다.

    Returns:
        DataFrame: Google Sheets 데이터
    """
    try:
        worksheet = connect_to_google_sheets()  # 워크시트 인증
        df = pd.DataFrame(worksheet.get_all_records())  # 워크시트 데이터를 DataFrame으로 변환
        time.sleep(0.1)
        return df
    except Exception as e:
        raise Exception(f"Google Sheets 데이터 읽기 실패: {e}")
