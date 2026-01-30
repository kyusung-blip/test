from google.oauth2.service_account import Credentials
import gspread
import streamlit as st

def get_gspread_client(service_key: str):
    """
    Streamlit Secrets에서 서비스 계정 키를 사용하여 동적으로 gspread 클라이언트를 생성합니다.
    - service_key: 'gcp_service_account_seobuk' 또는 'gcp_service_account_concise'
    """
    credentials = Credentials.from_service_account_info(st.secrets[service_key])
    return gspread.authorize(credentials)
