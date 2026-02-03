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
        gcp_key = os.getenv("GCP_SERVICE_KEY")
        if not gcp_key:
            raise ValueError(
                "GCP_SERVICE_KEY environment variable is not set. "
                "Please set this variable with your Google Cloud service account JSON credentials."
            )
        service_account_info = json.loads(gcp_key)
        credentials = Credentials.from_service_account_info(service_account_info)
        client = gspread.authorize(credentials)
        sheet_name = os.getenv("SPREADSHEET_NAME", "SEOBUK PROJECTION")
        worksheet_name = os.getenv("WORKSHEET_NAME", "NUEVO PROJECTION#2")
        worksheet = client.open(sheet_name).worksheet(worksheet_name)  # 워크시트 열기
        return worksheet
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse GCP_SERVICE_KEY as JSON: {e}")
    except Exception as e:
        raise Exception(f"Google Sheets 연결 실패: {e}")

# --- Google Sheets 데이터 읽기 ---
def read_google_sheets():
    """
    pandas DataFrame으로 Google Sheets 데이터를 반환합니다.
    
    Note: 이 함수는 Personal_path.Read_gspread()와 동일한 기능을 수행합니다.
    새로운 코드에서는 Personal_path.Read_gspread()를 사용하는 것을 권장합니다.

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

# --- Helper functions for compatibility ---
def _get_client():
    """
    인증된 gspread 클라이언트를 생성하여 반환합니다.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트
    """
    try:
        gcp_key = os.getenv("GCP_SERVICE_KEY")
        if not gcp_key:
            raise ValueError(
                "GCP_SERVICE_KEY environment variable is not set. "
                "Please set this variable with your Google Cloud service account JSON credentials."
            )
        service_account_info = json.loads(gcp_key)
        credentials = Credentials.from_service_account_info(service_account_info)
        client = gspread.authorize(credentials)
        return client
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse GCP_SERVICE_KEY as JSON: {e}")
    except Exception as e:
        raise Exception(f"Google Sheets 클라이언트 생성 실패: {e}")

def get_google_sheet(spreadsheet_name, worksheet_name):
    """
    지정된 스프레드시트와 워크시트를 열어서 워크시트 객체를 반환합니다.
    
    Args:
        spreadsheet_name (str): 스프레드시트 이름
        worksheet_name (str): 워크시트 이름
    
    Returns:
        gspread.Worksheet: 워크시트 객체
    """
    try:
        client = _get_client()
        worksheet = client.open(spreadsheet_name).worksheet(worksheet_name)
        return worksheet
    except Exception as e:
        raise Exception(f"워크시트 열기 실패: {e}")

def get_gspread_client_seobuk():
    """
    Seobuk 프로젝트용 gspread 클라이언트를 반환합니다.
    
    Note: 현재 이 함수는 _get_client()를 직접 호출합니다. 
    향후 별도의 서비스 계정이 필요한 경우 GCP_SERVICE_KEY_SEOBUK 
    환경 변수를 사용하도록 확장할 수 있습니다.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트
    """
    return _get_client()

def get_gspread_client_concise():
    """
    Concise 프로젝트용 gspread 클라이언트를 반환합니다.
    
    Note: 현재 이 함수는 _get_client()를 직접 호출합니다.
    향후 별도의 서비스 계정이 필요한 경우 GCP_SERVICE_KEY_CONCISE
    환경 변수를 사용하도록 확장할 수 있습니다.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트
    """
    return _get_client()
