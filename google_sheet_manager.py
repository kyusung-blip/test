import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@st.cache_resource
def get_spreadsheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    json_file = "concise-isotope-456307-n5-8cf3eb97b093.json"
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    gc = gspread.authorize(creds)
    return gc.open("Dealer Information")

def get_dealer_sheet():
    return get_spreadsheet().worksheet("시트1")

def get_company_sheet():
    return get_spreadsheet().worksheet("상사정보")
# google_sheet_manager.py 에 추가
def get_country_sheet():
    """'바이어나라정보' 워크시트 반환 (시트 이름이 다르면 수정하세요)"""
    return get_spreadsheet().worksheet("바이어")

def get_inventory_sheet():
    """Yard Status 시트 반환"""
    return get_spreadsheet_open("Inventory SEOBUK").worksheet("Yard Status")

def get_main_2026_sheet():
    """2026 메인 시트 반환"""
    return get_spreadsheet_open("Inventory SEOBUK").worksheet("2026")

def get_spreadsheet_open(name):
    # 기존에 정의된 시트 오픈 로직 사용
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    json_file = "concise-isotope-456307-n5-8cf3eb97b093.json"
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    gc = gspread.authorize(creds)
    return gc.open(name)
