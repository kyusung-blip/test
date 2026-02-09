import streamlit as st
import os
import sys
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. 유틸리티 및 데이터 설정 ---

# [이전 제공해주신 VINYEAR_map, color_map, ADDRESS_REGION_MAP 등은 상단에 유지되어 있다고 가정합니다]

def get_exchange_rate_logic():
    """우리은행 사이트에서 미국 달러 환율을 크롤링하여 세션 상태에 저장"""
    options = Options()
    options.add_argument("--headless")  # 서버 환경을 위한 headless 모드
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        # 1. 오늘 날짜 설정
        st.session_state['ex_date'] = datetime.today().strftime("%Y-%m-%d")

        # 2. WebDriver 설정
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://spot.wooribank.com/pot/Dream?withyou=FXXRT0011")
        
        # 조회 버튼 클릭
        search_button = driver.find_element(By.XPATH, '//*[@id="frm"]/fieldset/div/span/input')
        search_button.click()

        # 데이터 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[text()='미국 달러']"))
        )

        # 미국 달러 기준환율 크롤링
        xpath_expression = "//td[text()='미국 달러']/following-sibling::td[8]"
        rate = driver.find_element(By.XPATH, xpath_expression).text
        
        # 값 정제 및 저장
        cleaned_rate = re.sub(r',', '', rate)
        st.session_state['ex_rate'] = cleaned_rate
        
        st.toast(f"✅ 환율 크롤링 완료: {rate}원", icon="💰")

    except Exception as e:
        st.error(f"환율 정보를 가져오는 데 실패했습니다: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

# --- 2. Streamlit UI 및 세션 초기화 ---

if 'ex_rate' not in st.session_state:
    st.session_state['ex_rate'] = ""
if 'ex_date' not in st.session_state:
    st.session_state['ex_date'] = ""

st.set_page_config(layout="wide", page_title="차량 매매 통합 관리 시스템")

# --- 3. 화면 레이아웃 (좌 7 : 우 3) ---

col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    st.subheader("📋 상세 정보 입력")
    # [차량 기본 정보 등 기존 입력창들 위치]
    # ... (생략) ...

with col_right:
    st.subheader("💰 정산 및 결제 정보")
    st.text_input("차량대")
    st.text_input("계산서X")
    st.text_input("매도비")
    st.text_input("DECLARATION")
    st.text_input("합계금액")
    
    with st.expander("📝 세부 정산(Calculation)", expanded=True):
        st.text_input("계약금(만원)")
        st.text_input("잔금")
        
    with st.expander("⭐ 오토위니", expanded=True):
        st.text_input("업체명")
        # 크롤링된 날짜와 환율이 세션 상태를 통해 자동 입력됨
        st.text_input("환율기준일", value=st.session_state['ex_date'])
        
        c_ex1, c_ex2 = st.columns([3, 1])
        # 환율 칸: 크롤링 결과 반영
        c_ex1.text_input("환율", value=st.session_state['ex_rate'], key="exchange_input")
        
        c_ex2.markdown("<br>", unsafe_allow_html=True)
        if c_ex2.button("환율", help="우리은행 실시간 환율 조회"):
            with st.spinner("환율 정보를 가져오는 중..."):
                get_exchange_rate_logic()
                st.rerun() # 화면을 다시 그려서 업데이트된 값을 반영

        st.text_input("차량대금($)")
        st.text_input("영세율금액(원)")

    # [기타 버튼 및 플랫폼 정보]
    # ... (생략) ...
