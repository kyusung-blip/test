import streamlit as st
import os
import sys
import re
from datetime import datetime

# 크롤링 관련 라이브러리
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2 import service_account

# --- 1. 경로 및 설정 함수 ---
def resource_path(relative_path):
    """PyInstaller 및 클라우드 환경 대응 경로 함수"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- 2. 데이터 맵핑 사전 (제공 데이터) ---
VINYEAR_map = {
    "1": "2001", "2": "2002", "3": "2003", "4": "2004", "5": "2005", "6": "2006",
    "7": "2007", "8": "2008", "9": "2009", "A": "2010", "B": "2011", "C": "2012",
    "D": "2013", "E": "2014", "F": "2015", "G": "2016", "H": "2017", "J": "2018",
    "K": "2019", "L": "2020", "M": "2021", "N": "2022", "P": "2023", "R": "2024",
    "S": "2025", "T": "2026", "V": "2027"
}

color_map = {
    "silver gray": "GRAY", "sable": "BLACK", "rat color": "GRAY",
    "pearl gray": "WHITE", "mouse gray": "GRAY", "흰색": "WHITE",
    "검정색": "BLACK", "빨간색": "RED", "쥐색": "GRAY", "주황색": "ORANGE"
}

ADDRESS_REGION_MAP = {
    "서울": "서울", "인천": "인천", "김포": "김포", "양주": "양주", "용인": "용인",
    "광명": "광명", "의정부": "의정부", "부천": "부천", "수원": "수원", "부산": "부산",
    "대구": "대구", "대전": "대전", "울산": "울산", "세종": "세종", "광주": "광주"
}

# --- 3. 환율 크롤링 로직 ---
def get_exchange_rate():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        st.session_state['ex_date'] = datetime.today().strftime("%Y-%m-%d")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://spot.wooribank.com/pot/Dream?withyou=FXXRT0011")
        
        search_button = driver.find_element(By.XPATH, '//*[@id="frm"]/fieldset/div/span/input')
        search_button.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//td[text()='미국 달러']")))
        xpath_expression = "//td[text()='미국 달러']/following-sibling::td[8]"
        rate = driver.find_element(By.XPATH, xpath_expression).text
        
        st.session_state['ex_rate'] = re.sub(r',', '', rate)
        st.toast(f"환율 정보 로드 완료: {rate}", icon="💰")
    except Exception as e:
        st.error(f"환율 크롤링 실패: {e}")
    finally:
        if 'driver' in locals(): driver.quit()

# --- 4. Streamlit UI 및 세션 관리 ---
st.set_page_config(layout="wide", page_title="차량 매매 통합 시스템")

if 'ex_rate' not in st.session_state: st.session_state['ex_rate'] = ""
if 'ex_date' not in st.session_state: st.session_state['ex_date'] = ""

st.markdown("""
    <style>
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton, .stSelectbox { font-size: 10pt !important; }
    .output-box { background-color: #f8f9fa; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; min-height: 800px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. 화면 레이아웃 (7:3 분할) ---
col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    st.subheader("📋 차량 정보 입력")
    raw_input = st.text_area("데이터 붙여넣기 (Tab 구분)", height=70)
    st.divider()

    L_main, R_main = st.columns([1.1, 1])

    with L_main:
        st.markdown("**🚗 기본 정보**")
        v_num = st.text_input("차번호")
        
        # VIN 기반 연도 자동 매핑
        v_vin = st.text_input("VIN")
        detected_year = VINYEAR_map.get(v_vin[9].upper(), "") if len(v_vin) >= 10 else ""
        v_year = st.text_input("연식", value=detected_year)
        
        st.text_input("차명")
        st.text_input("차명(송금용)")
        
        c1, c2 = st.columns(2)
        v_km = c1.text_input("km")
        # 컬러 맵핑 적용
        raw_color = c2.text_input("color")
        v_color = color_map.get(raw_color.lower(), raw_color.upper()) if raw_color else ""
        
        # 주소 기반 지역 자동 매핑
        v_addr = st.text_input("주소")
        detected_region = next((val for key, val in ADDRESS_REGION_MAP.items() if key in v_addr), "")
        
        c3, c4 = st.columns(2)
        st.text_input("딜러연락처")
        st.text_input("지역", value=detected_region)

        with st.expander("🤝 딜러/판매자 정보", expanded=True):
            st.columns(2)[0].text_input("상사명")
            st.columns(2)[1].text_input("사업자번호")
        
        st.text_input("차량대계좌")
        st.text_input("매도비계좌")
        
        c7, c8, c9 = st.columns([2, 1, 1])
        c7.text_input("입금자명")
        c8.markdown("<br>", unsafe_allow_html=True); c8.button("계좌확인")
        c9.markdown("<br>", unsafe_allow_html=True); c9.button("정보추가&수정")

        c10, c11, c12 = st.columns([2, 1, 1])
        c10.text_input("바이어명"); c11.text_input("나라")
        c12.markdown("<br>", unsafe_allow_html=True); c12.button("확인")

    with R_main:
        st.markdown("**💰 정산 정보**")
        st.text_input("차량대"); st.text_input("계산서X"); st.text_input("매도비")
        st.text_input("DECLARATION"); st.text_input("합계금액")
        
        with st.expander("📝 세부 정산", expanded=True):
            st.text_input("계약금(만원)"); st.text_input("잔금")
            
        with st.expander("⭐ 오토위니", expanded=True):
            st.text_input("업체명")
            st.text_input("환율기준일", value=st.session_state['ex_date'])
            c_ex1, c_ex2 = st.columns([3, 1])
            c_ex1.text_input("환율", value=st.session_state['ex_rate'])
            c_ex2.markdown("<br>", unsafe_allow_html=True)
            if c_ex2.button("환율"):
                with st.spinner("조회 중..."):
                    get_exchange_rate()
                    st.rerun()
            st.text_input("차량대금($)"); st.text_input("영세율금액(원)")

        st.markdown("**🏷️ 기타 플랫폼**")
        st.columns(2)[0].text_input("사이트"); st.columns(2)[1].text_input("세일즈팀")
        st.columns(2)[0].selectbox("헤이딜러 종류", ["선택 안함", "제로", "셀프"])
        st.columns(2)[1].selectbox("헤이딜러 ID", ["선택 안함", "A", "B"])
        st.text_input("헤이딜러탁송")

    st.divider()
    st.markdown("**🛠️ 실행 제어**")
    btn_row = st.columns(6)
    btn_confirm = btn_row[0].button("확인후")
    btn_sms = btn_row[3].button("문자")
    # ... 나머지 버튼 생략

# --- 6. [우측 섹션] 결과 출력 ---
with col_right:
    st.subheader("📝 결과 출력")
    st.markdown('<div class="output-box">', unsafe_allow_html=True)
    if btn_confirm:
        st.success("데이터 확인 완료")
        st.write(f"변환 컬러: {v_color}")
        st.write(f"감지 지역: {detected_region}")
    elif btn_sms:
        st.info("문자 양식 생성됨")
    st.markdown('</div>', unsafe_allow_html=True)
