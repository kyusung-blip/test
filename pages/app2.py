import streamlit as st
import os
import re
from datetime import datetime

# 크롤링 관련 (클라우드 환경 대응)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. 설정 및 데이터 맵핑 ---
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

COLOR_MAP = {
    "silver gray": "GRAY", "sable": "BLACK", "rat color": "GRAY",
    "pearl gray": "WHITE", "mouse gray": "GRAY", "흰색": "WHITE", 
    "검정색": "BLACK", "빨간색": "RED", "쥐색": "GRAY", "주황색": "ORANGE"
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
        return "0"

def parse_money(value):
    try:
        # 숫자가 아닌 문자 제거 후 정수 변환
        clean_val = re.sub(r'[^0-9]', '', str(value))
        return int(clean_val) if clean_val else 0
    except:
        return 0

# --- 3. 환율 크롤링 (안정화 버전) ---
def get_exchange_rate():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # 깃허브/도커 환경에서 크롬 실행을 위한 필수 설정
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://spot.wooribank.com/pot/Dream?withyou=FXXRT0011")
        
        # 조회 버튼 클릭
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="frm"]/fieldset/div/span/input'))).click()
        
        # 환율 테이블 대기
        target_xpath = "//td[text()='미국 달러']/following-sibling::td[8]"
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, target_xpath)))
        
        rate = driver.find_element(By.XPATH, target_xpath).text
        st.session_state['ex_rate'] = rate.replace(",", "")
        st.session_state['ex_date'] = datetime.today().strftime("%Y-%m-%d")
        st.toast("환율 정보 로드 완료!", icon="💰")
    except Exception as e:
        st.error(f"환율 조회 실패: {e}")
    finally:
        if 'driver' in locals(): driver.quit()

# --- 4. 세션 상태 및 UI 초기화 ---
st.set_page_config(layout="wide", page_title="차량 매매 통합 시스템", page_icon="🚘")

if 'ex_rate' not in st.session_state: st.session_state['ex_rate'] = ""
if 'ex_date' not in st.session_state: st.session_state['ex_date'] = ""

# 스타일 적용 (폰트 크기 조절 및 레이아웃 최적화)
st.markdown("""
    <style>
    .stTextInput>div>div>input { font-size: 11pt !important; }
    .output-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 500px; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. 데이터 파싱 로직 ---
st.subheader("📋 데이터 입력 (Tab 구분)")
raw_input = st.text_area("엑셀/구글시트에서 복사한 데이터를 붙여넣으세요", height=100, placeholder="여기에 붙여넣기...")

# 파싱된 데이터를 담을 딕셔너리 초기화
p = {k: "" for k in IDX.keys()}

if raw_input:
    parts = raw_input.split('\t')
    for key, idx in IDX.items():
        if len(parts) > idx:
            p[key] = parts[idx].strip()
    
    # 로직: VIN 기반 연도 추출
    if len(p['vin']) >= 10:
        year_code = p['vin'][9].upper()
        p['year'] = VINYEAR_map.get(year_code, p['year'])
    
    # 로직: 컬러 맵핑
    p['color'] = COLOR_MAP.get(p['color'].lower(), p['color'])
    
    # 로직: 주소 기반 지역 추출
    for keyword, region in ADDRESS_REGION_MAP.items():
        if keyword in p['address']:
            p['region'] = region
            break

# --- 6. 메인 화면 구성 ---
col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    L_main, R_main = st.columns(2)

    with L_main:
        st.markdown("### 🚗 차량 정보")
        v_plate = st.text_input("차량 번호", value=p['plate'])
        v_car_name = st.text_input("모델명", value=p['car_name'])
        v_vin = st.text_input("차대번호(VIN)", value=p['vin'])
        
        c1, c2 = st.columns(2)
        v_year = c1.text_input("연식", value=p['year'])
        v_km = c2.text_input("주행거리(km)", value=p['km'])
        
        c3, c4 = st.columns(2)
        v_color = c3.text_input("색상", value=p['color'])
        v_region = c4.text_input("지역", value=p['region'])
        
        v_addr = st.text_input("상세 주소", value=p['address'])
        v_phone = st.text_input("딜러 연락처", value=p['dealer_phone'])

        with st.expander("👤 바이어 및 계좌 정보"):
            v_buyer = st.text_input("바이어명", value=p['buyer'])
            st.text_input("입금자명")
            st.text_input("입금 계좌번호")

    with R_main:
        st.markdown("### 💰 정산 정보")
        v_price = st.text_input("차량 대금", value=format_number(p['price']))
        v_fee = st.text_input("매도비", value=format_number(p['fee']))
        v_contract = st.text_input("계약금", value="0")
        
        # 합계 자동 계산
        total_val = parse_money(v_price) + parse_money(v_fee)
        st.markdown(f"**총 합계: {total_val:,} 원**")
        
        with st.expander("🌐 플랫폼 및 환율", expanded=True):
            st.text_input("사이트", value=p['site'])
            st.text_input("세일즈팀", value=p['sales'])
            if st.button("🔄 우리은행 환율 가져오기"):
                get_exchange_rate()
                st.rerun()
            st.text_input("현재 환율", value=st.session_state['ex_rate'])
            st.caption(f"기준일자: {st.session_state['ex_date']}")

    st.divider()
    # 하단 버튼 레이아웃
    st.markdown("### 🛠️ 실행 메뉴")
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    btn_confirm = b_col1.button("✅ 데이터 확정", use_container_width=True)
    btn_sms = b_col2.button("📱 문자 발송 양식", use_container_width=True)
    btn_remit = b_col3.button("💸 송금 요청", use_container_width=True)
    btn_reset = b_col4.button("♻️ 내용 초기화", type="secondary", use_container_width=True)

# --- 7. 우측 결과 출력 섹션 ---
with col_right:
    st.markdown("### 📝 결과 프리뷰")
    output_container = st.container()
    
    with output_container:
        if btn_confirm:
            st.success("데이터가 정리되었습니다.")
            res_text = f"""[차량 정보 확정]
• 번호: {v_plate}
• 모델: {v_car_name}
• 연식: {v_year}
• 주행: {v_km}km
• 지역: {v_region}
• 합계: {total_val:,}원"""
            st.code(res_text, language=None)
            st.button("📋 복사하기 (준비중)")
        
        elif btn_sms:
            sms_text = f"[{v_plate}] 매입 진행합니다. {v_region} 탁송 기사님 배정 후 연락드리겠습니다."
            st.info("문자 발송 양식")
            st.code(sms_text, language=None)

        elif btn_reset:
            st.rerun()
        
        else:
            st.markdown('<div class="output-box">왼쪽의 버튼을 클릭하면 결과가 생성됩니다.</div>', unsafe_allow_html=True)
