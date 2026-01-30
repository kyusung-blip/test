from google.oauth2.service_account import Credentials
import gspread
import streamlit as st

@st.cache_resource
def get_credentials(service_key: str, _scopes=None):
    """
    Streamlit Secrets에서 Google 인증 정보를 가져옵니다.
    
    Args:
        service_key: Streamlit secrets의 키 (예: 'gcp_service_account')
        _scopes: Optional tuple of OAuth scopes. Use underscore prefix to exclude from cache key.
                The scopes should be passed as a tuple for proper caching behavior.
    
    Returns:
        Credentials: Google OAuth2 credentials 객체
    """
    if _scopes:
        return Credentials.from_service_account_info(st.secrets[service_key], scopes=_scopes)
    else:
        return Credentials.from_service_account_info(st.secrets[service_key])

@st.cache_resource
def get_gspread_client(service_key: str, _scopes=None):
    """
    Streamlit Secrets에서 서비스 계정 키를 사용하여 동적으로 gspread 클라이언트를 생성합니다.
    
    Args:
        service_key: Streamlit secrets의 키 (예: 'gcp_service_account_seobuk', 'gcp_service_account')
        _scopes: Optional tuple of OAuth scopes. Use underscore prefix to exclude from cache key.
                If None, credentials will use service account's default scopes.
                The scopes should be passed as a tuple for proper caching behavior.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트
    """
    credentials = get_credentials(service_key, _scopes=_scopes)
    return gspread.authorize(credentials)

def get_gspread_client_seobuk():
    """
    Seobuk 프로젝트용 gspread 클라이언트를 생성합니다.
    
    Note: 캐싱은 내부 get_gspread_client() 함수에서 처리됩니다.
    
    Returns:
        gspread.Client: Seobuk 서비스 계정으로 인증된 gspread 클라이언트
    """
    return get_gspread_client("gcp_service_account_seobuk")

def get_gspread_client_concise():
    """
    Concise 프로젝트용 gspread 클라이언트를 생성합니다.
    
    Note: 캐싱은 내부 get_gspread_client() 함수에서 처리됩니다.
    
    Returns:
        gspread.Client: Concise 서비스 계정으로 인증된 gspread 클라이언트
    """
    return get_gspread_client("gcp_service_account_concise")

def get_google_sheet(sheet_name: str, worksheet_name: str, service_key: str = "gcp_service_account", scopes=None):
    """
    Google Sheets 워크시트에 연결합니다.
    
    Note: 이 함수는 gspread 클라이언트를 캐시하지만, 워크시트 객체 자체는 캐시하지 않습니다.
    워크시트 데이터가 외부에서 수정되면 다시 호출하여 최신 데이터를 가져와야 합니다.
    
    Args:
        sheet_name: Google Sheets 문서 이름
        worksheet_name: 워크시트 이름
        service_key: Streamlit secrets의 키 (기본값: 'gcp_service_account')
        scopes: Optional list of OAuth scopes. If None, defaults to spreadsheets and drive access.
    
    Returns:
        gspread.Worksheet: 연결된 워크시트 객체
    """
    # Normalize scopes to tuple for consistent caching behavior
    if scopes is None:
        scopes = ("https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive")
    else:
        scopes = tuple(scopes) if not isinstance(scopes, tuple) else scopes
    
    gc = get_gspread_client(service_key, _scopes=scopes)
    return gc.open(sheet_name).worksheet(worksheet_name)
