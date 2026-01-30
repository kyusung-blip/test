from google.oauth2.service_account import Credentials
import gspread
import streamlit as st

def get_gspread_client(service_key: str, scopes=None):
    """
    Streamlit Secrets에서 서비스 계정 키를 사용하여 동적으로 gspread 클라이언트를 생성합니다.
    
    Args:
        service_key: Streamlit secrets의 키 (예: 'gcp_service_account_seobuk', 'gcp_service_account')
        scopes: Optional list of OAuth scopes. If None, uses gspread defaults.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트
    """
    if scopes:
        credentials = Credentials.from_service_account_info(st.secrets[service_key], scopes=scopes)
    else:
        credentials = Credentials.from_service_account_info(st.secrets[service_key])
    return gspread.authorize(credentials)

def get_gspread_client_seobuk():
    """
    Seobuk 프로젝트용 gspread 클라이언트를 생성합니다.
    
    Returns:
        gspread.Client: Seobuk 서비스 계정으로 인증된 gspread 클라이언트
    """
    return get_gspread_client("gcp_service_account_seobuk")

def get_gspread_client_concise():
    """
    Concise 프로젝트용 gspread 클라이언트를 생성합니다.
    
    Returns:
        gspread.Client: Concise 서비스 계정으로 인증된 gspread 클라이언트
    """
    return get_gspread_client("gcp_service_account_concise")

def get_credentials(service_key: str, scopes=None):
    """
    Streamlit Secrets에서 Google 인증 정보를 가져옵니다.
    
    Args:
        service_key: Streamlit secrets의 키 (예: 'gcp_service_account')
        scopes: Optional list of OAuth scopes
    
    Returns:
        Credentials: Google OAuth2 credentials 객체
    """
    if scopes:
        return Credentials.from_service_account_info(st.secrets[service_key], scopes=scopes)
    else:
        return Credentials.from_service_account_info(st.secrets[service_key])

def get_google_sheet(sheet_name: str, worksheet_name: str, service_key: str = "gcp_service_account", scopes=None):
    """
    Google Sheets 워크시트에 연결합니다.
    
    Args:
        sheet_name: Google Sheets 문서 이름
        worksheet_name: 워크시트 이름
        service_key: Streamlit secrets의 키 (기본값: 'gcp_service_account')
        scopes: Optional list of OAuth scopes. If None, uses default scopes.
    
    Returns:
        gspread.Worksheet: 연결된 워크시트 객체
    """
    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    gc = get_gspread_client(service_key, scopes=scopes)
    return gc.open(sheet_name).worksheet(worksheet_name)
