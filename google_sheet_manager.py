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
# google_sheet_manager.py 에 추가
def get_inspection_data_sheet():
    """인스펙션 상세 내용 시트 반환"""
    # 스프레드시트 이름과 워크시트 이름을 정확히 지정합니다.
    return get_spreadsheet_open("Inspection Organization (24-23)").worksheet("인스팩션내용")

def get_nuevo_projection_sheet():
    """'SEOBUK PROJECTION' 스프레드시트의 'NUEVO PROJECTION#2' 워크시트 반환"""
    return get_spreadsheet_open("SEOBUK PROJECTION").worksheet("NUEVO PROJECTION#2")

def get_crawling_queue_sheet():
    """'SEOBUK PROJECTION' 스프레드시트의 'Crawling_Queue' 워크시트 반환"""
    return get_spreadsheet_open("SEOBUK PROJECTION").worksheet("Crawling_Queue")

# google_sheet_manager.py

@st.cache_data(ttl=600)  # 10분간 캐시 유지
def get_car_name_map():
    """'차명' 시트에서 매핑 정보를 읽어 딕셔너리로 반환"""
    try:
        # 기존 정의된 get_spreadsheet 사용
        spreadsheet = get_spreadsheet() 
        sheet = spreadsheet.worksheet("차명")
        all_values = sheet.get_all_values()

        if len(all_values) < 2:
            return {}

        # { "검색키": "변환될이름" } 형태의 딕셔너리 생성
        car_name_map = {}
        for row in all_values[1:]:  # 헤더 제외
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                car_name_map[row[0].strip().upper()] = row[1].strip()
        
        return car_name_map
    except Exception as e:
        st.error(f"차명 매핑 로드 실패: {e}")
        return {}

# google_sheet_manager.py 에 추가

def get_no_by_plate(plate_number):
    """
    'Inventory SEOBUK' 시트의 '2026' 워크시트에서
    D열(차량번호)을 검색하여 일치하는 행의 B열(NO.) 값을 반환
    """
    try:
        sheet = get_main_2026_sheet()
        # D열(차량번호) 데이터 전체를 가져옵니다.
        # col_values(4)는 D열입니다.
        d_col = sheet.col_values(4)
        
        # 정확히 일치하는 값의 인덱스 찾기 (1부터 시작하는 인덱스)
        try:
            row_idx = d_col.index(plate_number.strip()) + 1
            # 해당 행의 B열(2번째 열) 값을 가져옵니다.
            no_value = sheet.cell(row_idx, 2).value
            return no_value
        except ValueError:
            # 일치하는 차량번호가 없는 경우
            return None
    except Exception as e:
        st.error(f"구글 시트 NO. 조회 실패: {e}")
        return None
