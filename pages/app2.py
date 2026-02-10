import streamlit as st
import os
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

# --- 1. 설정 및 인덱스 정의 (기존 로직 유지) ---
IDX = {
    "site": 1, "sales": 2, "year": 5, "car_name": 6, "km": 9,
    "plate": 10, "vin": 11, "heydlr_delivery": 12, "color": 13,
    "address": 16, "dealer_phone": 18, "region": 19, "price": 22,
    "contract": 23, "fee": 24, "balance": 21, "buyer": 32
}

VINYEAR_map = {
    "1": "2001", "2": "2002", "3": "2003", "4": "2004", "5": "2005", "6": "2006",
    "7": "2007", "8": "2008", "9": "2009", "A": "2010", "B": "2011", "C": "2012",
    "D": "2013", "E": "2014", "F": "2015", "G": "2016", "H": "2017", "J": "2018",
    "K": "2019", "L": "2020", "M": "2021", "N": "2022", "P": "2023", "R": "2024",
    "S": "2025", "T": "2026", "V": "2027"
}

color_map = {
    "silver gray": "GRAY", "Silver gray": "GRAY", "sable": "BLACK", "rat color": "GRAY",
    "pearl gray": "WHITE", "mouse gray": "GRAY", "흰색": "WHITE", "검정색": "BLACK",
    "빨간색": "RED", "쥐색": "GRAY", "주황색": "ORANGE"
}

ADDRESS_REGION_MAP = {
    "서울": "서울", "인천": "인천", "김포": "김포", "양주": "양주", "용인": "용인",
    "광명": "광명", "의정부": "의정부", "부천": "부천", "수원": "수원", "부산": "부산",
    "대구": "대구", "대전": "대전", "울산": "울산", "세종": "세종", "광주": "광주"
}

# --- 2. 헬퍼 함수 및 환율 크롤링 ---
def format_number(value):
    try:
        val = int(str(value).replace(",", "").strip())
        return f"{val:,}"
    except: return value

def parse_money(value):
    try:
        return int(re.sub(r'[^0-9]', '', str(value)))
    except: return 0

def get_exchange_rate():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://spot.wooribank.com/pot/Dream?withyou=FXXRT0011")
        driver.find_element(By.XPATH, '//*[@id="frm"]/fieldset/div/span/input').click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//td[text()='미국 달러']")))
        rate = driver.find_element(By.XPATH, "//td[text()='미국 달러']/following-sibling::td[8]").text
        st.session_state['ex_rate'] = rate.replace(",", "")
        st.session_state['ex_date'] = datetime.today().strftime("%Y-%m-%d")
        st.toast("환율 정보 로드 완료!", icon="💰")
    except Exception as e:
        st.error(f"환율 조회 실패: {e}")
    finally:
        if 'driver' in locals(): driver.quit()

# --- 3. UI 및 세션 초기화 ---
st.set_page_config(layout="wide", page_title="차량 매매 통합 시스템")

if 'ex_rate' not in st.session_state: st.session_state['ex_rate'] = ""
if 'ex_date' not in st.session_state: st.session_state['ex_date'] = ""
if 'output_text' not in st.session_state: st.session_state['output_text'] = ""

st.markdown("""
    <style>
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton { font-size: 10pt !important; }
    .stButton>button { width: 100%; border-radius: 4px; height: 35px; margin-bottom: 2px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 40px; white-space: pre-wrap; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 상단 데이터 입력 파싱 (기존 로직) ---
st.subheader("📋 데이터 붙여넣기")
raw_input = st.text_area("탭 구분 데이터를 여기에 붙여넣으세요", height=70)

parsed = {k: "" for k in IDX.keys()}
if raw_input:
    parts = raw_input.split('\t')
    for key, idx in IDX.items():
        if len(parts) > idx:
            parsed[key] = parts[idx].strip()
    
    if len(parsed['vin']) >= 10:
        year_code = parsed['vin'][9].upper()
        parsed['year'] = VINYEAR_map.get(year_code, parsed['year'])
    
    parsed['color'] = color_map.get(parsed['color'].lower(), parsed['color'].upper())
    
    for keyword, region in ADDRESS_REGION_MAP.items():
        if keyword in parsed['address']:
            parsed['region'] = region
            break

# --- 5. 메인 레이아웃 (35% : 35% : 30%) ---
col_left, col_mid, col_right = st.columns([0.35, 0.35, 0.30])

with col_left:
    st.markdown("**🚗 차량 기본 정보**")
    v_plate = st.text_input("차번호", value=parsed['plate'])
    v_year = st.text_input("연식", value=parsed['year'])
    v_car_name = st.text_input("차명", value=parsed['car_name'])
    v_vin = st.text_input("VIN", value=parsed['vin'])
    
    c1, c2 = st.columns(2)
    v_km = c1.text_input("km", value=parsed['km'])
    v_color = c2.text_input("color", value=parsed['color'])
    
    v_addr = st.text_input("주소", value=parsed['address'])
    c3, c4 = st.columns(2)
    v_phone = c3.text_input("딜러연락처", value=parsed['dealer_phone'])
    v_region = c4.text_input("지역", value=parsed['region'])

    with st.expander("👤 거래처/바이어 정보", expanded=True):
        st.text_input("상사명")
        st.text_input("바이어명", value=parsed['buyer'])
        st.text_input("나라")

with col_mid:
    st.markdown("**💰 정산 및 결제 정보**")
    v_price = st.text_input("차량대", value=format_number(parsed['price']))
    v_fee = st.text_input("매도비", value=format_number(parsed['fee']))
    v_contract_input = st.text_input("계약금(만원)", value="0")
    
    # 합계 계산
    total_val = parse_money(v_price) + parse_money(v_fee)
    st.markdown(f"**합계금액: :blue[{total_val:,}] 원**")
    
    with st.expander("⭐ 오토위니 / 플랫폼", expanded=True):
        st.text_input("사이트", value=parsed['site'])
        st.text_input("세일즈팀", value=parsed['sales'])
        cex1, cex2 = st.columns([3, 1])
        cex1.text_input("환율", value=st.session_state['ex_rate'])
        if cex2.button("환율조회"): 
            get_exchange_rate()
            st.rerun()
            
    st.selectbox("헤이딜러 종류", ["선택 안함", "제로", "셀프"])
    st.text_input("헤이딜러탁송", value=parsed['heydlr_delivery'])

with col_right:
    st.markdown("**📝 리스트 탭**")
    tab_msg, tab_remit, tab_etc = st.tabs(["메시지출력", "송금요청", "기타"])
    
    with tab_msg:
        r1 = st.columns(3)
        if r1[0].button("확인후"): st.session_state.output_text = f"[{v_plate}] 확인 완료"
        if r1[1].button("세일즈팀"): st.session_state.output_text = f"세일즈팀 전달: {v_car_name} ({v_plate})"
        if r1[2].button("검수자"): st.session_state.output_text = f"검수요청: {v_plate} ({v_region})"
        
        r2 = st.columns(3)
        if r2[0].button("문자"): st.session_state.output_text = f"매입확정: {v_plate} 탁송 준비중"
        if r2[1].button("아웃소싱"): st.session_state.output_text = f"아웃소싱 의뢰: {v_plate}"
        if r2[2].button("주소공유"): st.session_state.output_text = f"탁송 주소: {v_addr}"
        
        if st.button("서류문자"): st.session_state.output_text = "서류 준비: 등록증 원본, 인감증명서"

    with tab_remit:
        r3 = st.columns(2)
        if r3[0].button("일반매입"): st.session_state.output_text = f"일반매입 송금요청\n{v_plate}\n{total_val:,}원"
        if r3[1].button("폐자원매입"): st.session_state.output_text = f"폐자원 송금요청\n{v_plate}"
        
        r4 = st.columns(2)
        if r4[0].button("계약금"): st.session_state.output_text = f"계약금 송금요청: {v_plate}"
        if r4[1].button("폐자원계약"): st.session_state.output_text = f"폐자원 계약금: {v_plate}"
        
        r5 = st.columns(2)
        if r5[0].button("송금완료"): st.session_state.output_text = f"송금 완료: {v_plate}"
        if r5[1].button("계약금송금완료"): st.session_state.output_text = f"계약금 송금 완료: {v_plate}"
        
        r6 = st.columns(2)
        if r6[0].button("오토위니"): st.session_state.output_text = f"오토위니 정산: {v_plate}"
        if r6[1].button("헤이딜러"): st.session_state.output_text = f"헤이딜러 정산: {v_plate}"

    with tab_etc:
        if st.button("입고방"): st.session_state.output_text = f"입고 알림: {v_plate} ({v_car_name})"
        if st.button("사이트"): st.session_state.output_text = f"사이트: {parsed['site']}"

    st.markdown("---")
    # 메시지 출력 결과 및 컨트롤
    st.session_state.output_text = st.text_area("결과 메시지", value=st.session_state.output_text, height=250)
    
    cb1, cb2 = st.columns(2)
    if cb1.button("📋 내용복사"):
        st.toast("내용이 선택되었습니다. Ctrl+C를 눌러주세요.")
    if cb2.button("♻️ 내용리셋"):
        st.session_state.output_text = ""
        st.rerun()
