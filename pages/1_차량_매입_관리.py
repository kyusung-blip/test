import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import re

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 - 차량 매입 관리", layout="wide")

# --- 1. 보안 설정 및 시트 연결 ---
def get_google_sheet(sheet_name, worksheet_name):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Streamlit Secrets에 저장된 정보를 사용합니다.
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    return gc.open(sheet_name).worksheet(worksheet_name)

# --- 2. 로직 함수 (기존 GUI.py에서 가져온 핵심 로직) ---
def parse_money(value_raw):
    if not value_raw: return 0
    value_raw = str(value_raw).replace(",", "").replace(" ", "")
    number_match = re.search(r"([\d\.]+)", value_raw)
    if not number_match: return 0
    number = float(number_match.group(1))
    if "만원" in value_raw: number *= 10000
    return int(number)

# --- 3. 웹 UI 구성 ---
st.title("🚗 차량 정보 자동화 시스템 (Web)")

# 사이드바: 옥션/헤이딜러 옵션
with st.sidebar:
    st.header("⚙️ 옵션 설정")
    auction_choice = st.selectbox("옥션 선택", ["선택 안함", "현대글로비스", "오토허브", "롯데", "K car"])
    heydlr_choice = st.selectbox("헤이딜러 타입", ["선택 안함", "일반", "제로", "바로낙찰"])

# 메인 화면: 탭으로 구분
tab1, tab2 = st.tabs(["📋 정보 입력 및 등록", "🔍 딜러/바이어 조회"])

with tab1:
    # 데이터 붙여넣기 영역
    raw_input = st.text_area("📋 데이터를 여기에 붙여넣으세요 (Tab 구분)", height=100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("기본 정보")
        plate = st.text_input("차번호 (Vehicle Number)")
        vin = st.text_input("VIN (차대번호)")
        car_name = st.text_input("차명 (Model)")
        car_name_alt = st.text_input("차명 - 송금용 (캐시 연동)")
        km = st.text_input("주행거리 (km)")
        
    with col2:
        st.subheader("금액 및 계좌")
        price = st.text_input("차량대 (Vehicle Price)", value="0")
        fee = st.text_input("매도비 (Sales Fee)", value="0")
        contract = st.text_input("계산서X 금액", value="0")
        
        # 합계 자동 계산 표시
        total_val = parse_money(price) + parse_money(fee) + parse_money(contract)
        st.info(f"💰 현재 합계 금액: {total_val:,}원")

    # 버튼 영역
    if st.button("🚀 인벤토리 및 메인 시트 등록", use_container_width=True):
        with st.spinner('구글 시트에 데이터를 등록 중입니다...'):
            try:
                # 여기에 실제 등록 로직(append_row 등) 구현 가능
                # 예시: 메인 시트 연결 테스트
                main_sheet = get_google_sheet("Inventory SEOBUK", "2026")
                st.success("✅ [테스트] 구글 시트 연결 및 등록 준비 완료!")
            except Exception as e:
                st.error(f"❌ 등록 중 오류 발생: {e}")

with tab2:
    st.subheader("🔎 딜러 정보 검색")
    search_phone = st.text_input("딜러 연락처 입력 (숫자만)")
    if st.button("조회하기"):
        st.warning("이 기능은 현재 구현 준비 중입니다.")

# --- 4. 툴킷 ---
st.divider()
st.caption("서북인터내셔널 차량 정보 자동 추출기 - Web v1.0")
