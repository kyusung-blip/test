import streamlit as st
import os
import sys
import re
from datetime import datetime

# 크롤링 및 인증 관련
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. 설정 및 인덱스 정의 (GUI.py 기준) ---
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

# --- 2. 헬퍼 함수 ---
def format_number(value):
    try:
        val = int(str(value).replace(",", "").strip())
        return f"{val:,}"
    except:
        return value

def parse_money(value):
    try:
        return int(str(value).replace(",", "").replace("원", "").replace("만원", "0000").strip())
    except:
        return 0

# --- 3. 환율 크롤링 함수 ---
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

# --- 4. UI 설정 ---
st.set_page_config(layout="wide", page_title="차량 매매 통합 시스템")

if 'ex_rate' not in st.session_state: st.session_state['ex_rate'] = ""
if 'ex_date' not in st.session_state: st.session_state['ex_date'] = ""

st.markdown("""
    <style>
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton { font-size: 10pt !important; }
    .output-box { background-color: #f8f9fa; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; min-height: 850px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. 데이터 파싱 로직 (GUI.py 스타일) ---
parsed = {k: "" for k in IDX.keys()}
st.subheader("📋 데이터 붙여넣기")
raw_input = st.text_area("탭 구분 데이터를 여기에 붙여넣으세요", height=70)

if raw_input:
    parts = raw_input.split('\t')
    for key, idx in IDX.items():
        if len(parts) > idx:
            parsed[key] = parts[idx].strip()
    
    # VIN 기반 연도 자동 추출
    if len(parsed['vin']) >= 10:
        year_code = parsed['vin'][9].upper()
        parsed['year'] = VINYEAR_map.get(year_code, parsed['year'])
    
    # 컬러 맵핑
    parsed['color'] = color_map.get(parsed['color'].lower(), parsed['color'].upper())
    
    # 주소 기반 지역 맵핑
    for keyword, region in ADDRESS_REGION_MAP.items():
        if keyword in parsed['address']:
            parsed['region'] = region
            break

# --- 6. 메인 화면 구성 (7:3 분할) ---
col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    L_main, R_main = st.columns([1.1, 1])

    with L_main:
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

        with st.expander("🤝 딜러/판매자 정보", expanded=True):
            st.columns(2)[0].text_input("상사명")
            st.columns(2)[1].text_input("사업자번호")
        
        st.text_input("차량대계좌")
        st.columns([2,1,1])[0].text_input("입금자명")
        st.columns([2,1,1])[1].markdown("<br>", unsafe_allow_html=True)
        st.columns([2,1,1])[1].button("계좌확인")
        
        st.columns([2,1,1])[0].text_input("바이어명", value=parsed['buyer'])
        st.columns([2,1,1])[1].text_input("나라")
        st.columns([2,1,1])[2].markdown("<br>", unsafe_allow_html=True)
        st.columns([2,1,1])[2].button("확인")

    with R_main:
        st.markdown("**💰 정산 및 결제 정보**")
        v_price = st.text_input("차량대", value=format_number(parsed['price']))
        st.text_input("계산서X", value=format_number(parsed['contract']))
        v_fee = st.text_input("매도비", value=format_number(parsed['fee']))
        st.text_input("DECLARATION")
        
        # 합계 계산
        total_val = parse_money(v_price) + parse_money(v_fee)
        st.text_input("합계금액", value=f"{total_val:,}")

        with st.expander("세부 정산(Calculation)", expanded=True):
            st.text_input("계약금(만원)")
            st.text_input("잔금", value=format_number(parsed['balance']))
            
        with st.expander("⭐ 오토위니", expanded=True):
            st.text_input("업체명")
            st.text_input("환율기준일", value=st.session_state['ex_date'])
            cex1, cex2 = st.columns([3, 1])
            cex1.text_input("환율", value=st.session_state['ex_rate'])
            cex2.markdown("<br>", unsafe_allow_html=True)
            if cex2.button("환율"): get_exchange_rate(); st.rerun()

        st.markdown("**🏷️ 플랫폼 정보**")
        st.columns(2)[0].text_input("사이트", value=parsed['site'])
        st.columns(2)[1].text_input("세일즈팀", value=parsed['sales'])
        st.selectbox("헤이딜러 종류", ["선택 안함", "제로", "셀프"])
        st.text_input("헤이딜러탁송", value=parsed['heydlr_delivery'])

    st.divider()
    st.markdown("**🛠️ 실행 제어**")
    row1 = st.columns(6)
    btn_confirm = row1[0].button("확인후")
    btn_sales = row1[1].button("세일즈팀")
    btn_sms = row1[3].button("문자")
    
    row2 = st.columns(6)
    btn_remit = row2[3].button("송금완료")
    btn_reset = row2[5].button("내용리셋", type="secondary")

# --- 7. 우측 결과 출력 섹션 ---
with col_right:
    st.subheader("📝 결과 출력")
    st.markdown('<div class="output-box">', unsafe_allow_html=True)
    if btn_confirm:
        st.success(f"[{v_plate}] 확인 완료")
        st.code(f"차량명: {v_car_name}\n번호: {v_plate}\n지역: {v_region}", language=None)
    elif btn_reset:
        st.rerun()
    else:
        st.write("버튼을 클릭하면 결과가 표시됩니다.")
    st.markdown('</div>', unsafe_allow_html=True)
