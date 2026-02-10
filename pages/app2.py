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

# --- 1. 설정 및 인덱스 정의 (기존 유지) ---
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

# --- 2. 유틸리티 함수 ---
def format_number(value):
    try:
        val = int(str(value).replace(",", "").strip())
        return f"{val:,}"
    except: return str(value)

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

# --- 3. 메시지 생성 핵심 로직 (기존 Tkinter 이식) ---
def generate_message(m_type, d, category="msg"):
    year = d['year']
    car_name = d['car_name'] or "차량명"
    plate = d['plate']
    
    # 값 정규화
    raw_p = d['price'].strip()
    raw_p_norm = "" if re.fullmatch(r'0|0원|0만원', raw_p) else raw_p
    raw_f = d['fee'].strip()
    raw_f_norm = "" if re.fullmatch(r'0|0원|0만원', raw_f) else raw_f
    raw_c = d['contract_x'].strip()
    raw_c_norm = "" if re.fullmatch(r'0|0원|0만원', raw_c) else raw_c

    title_line = f"{year} {car_name}"
    name_line = f"{d['sender']}로" if d['sender'] == "차량번호" else f"{d['sender']}으로"

    # [Category 1: 일반 메시지 출력]
    if category == "msg":
        if m_type == "아웃소싱":
            return f"요청자 : {d['sales']}\n차명 : {d['car_name']}\n차량번호 : {d['plate']}\n주소 : {d['address']}\n차주 연락처 : {d['phone']}\n\n{d['region']} 한대 부탁드립니다~!\n\n{d['site']}\n"
        elif m_type == "주소공유":
            return f"Sales Team : {d['sales']}\nModel : {d['car_name']}\nPlate : {d['plate']}\nCar Address : {d['address']}\nDealer Phone : {d['phone']}\n\n{d['site']}\n"
        elif m_type == "서류문자":
            return "필요서류: 자동차등록증 원본, 사업자등록증 사본(있는경우), 인감증명서(자동차매도용)입니다."
        else:
            # 확인후, 세일즈팀, 검수자, 문자 공통 로직
            if raw_p_norm and raw_f_norm and raw_c_norm:
                res = f"{title_line}\n{plate}\n\n수출말소기준\n계산서(O) : {raw_p}\n계산서(X) : {raw_c}\n매도비 : {raw_f}"
            elif raw_p_norm and raw_c_norm and not raw_f_norm:
                res = f"{title_line}\n{plate}\n\n수출말소기준\n계산서(O) : {raw_p}\n계산서(X) : {raw_c}"
            elif raw_p_norm and raw_f_norm and not raw_c_norm:
                res = f"{title_line}\n{plate}\n\n수출말소기준\n차량대 : {raw_p}\n매도비 : {raw_f}\n세금계산서 전액발행"
            else:
                fee_txt = f"매도비 : {raw_f}" if raw_f_norm else f"매도비포함 {raw_p}"
                res = f"{title_line}\n{plate}\n\n수출말소기준\n{fee_txt}\n세금계산서 전액발행"
            
            if m_type == "세일즈팀": res += "\n\n세일즈팀에서 금일 방문 예정입니다~!"
            elif m_type == "검수자": res += "\n\n검수자 배정 후 연락드리겠습니다~!"
            elif m_type == "확인후": res += "\n\n확인 후 연락드리겠습니다~!"
            return res

    # [Category 2: 송금 요청]
    elif category == "remit":
        price_val = parse_money(raw_p_norm)
        deposit_val = parse_money(d['deposit'])
        calc_minus_deposit = price_val - (deposit_val * 10000 if deposit_val < 5000 else deposit_val)
        raw_calc_minus_deposit = format_number(calc_minus_deposit)

        msg = "*서북인터내셔널"
        if m_type in ["계약금", "일반매입", "송금완료", "폐자원매입", "계약금 송금완료"]:
            msg += f" 주식회사*\n\n"
            if m_type == "폐자원매입": msg += "@@@폐자원매입@@@\n\n"
            elif "완료" in m_type: msg += "@@@송금완료@@@\n\n"
            
            msg += f"차번호: {plate} // {title_line}\nVIN: {d['vin']}\n\n사업자번호: {d['biz_num']}\n주소: {d['address']}\n번호: {d['phone']}\n\n"
            
            if raw_p_norm and raw_c_norm: # 분리매입
                msg += f"계산서(O): {raw_p}\n계산서(X): {raw_c}\n"
                if raw_f_norm: msg += f"매도비: {raw_f}\n"
                msg += f"합계: {d['total']}\n\n계좌\n계산서(O): {d['acc_o']}\n계산서(X): {d['acc_x']}\n"
            else: # 일반매입
                fee_line = f"매도비: {raw_f}" if raw_f_norm else "매도비포함"
                msg += f"차량대: {raw_p}\n{fee_line}\n합계: {d['total']}\n\n계좌\n차량대: {d['acc_o']}\n"
            
            if raw_f_norm and d['acc_fee']: msg += f"매도비: {d['acc_fee']}\n"
            
            if "계약금" in m_type:
                fee_part = f"+{raw_f}" if raw_f_norm else ""
                contract_part = f"+{raw_c}" if raw_c_norm else ""
                final_calc = f"{raw_calc_minus_deposit}{contract_part}{fee_part}"
                msg += f"\n{name_line} 계약금 송금 부탁드립니다.\n\n@@@계약금 {d['deposit']} " + ("/ 송금완료" if "완료" in m_type else "") + f"\n@@@잔금 {final_calc if '완료' not in m_type else d['final_bal']}"
            else:
                msg += f"\n{name_line} 송금 부탁드립니다."
            return msg

        elif m_type == "오토위니":
            return f"-{d['company']}*\n*서북인터내셔널-{d['company']}*\n\n모델: {year} {d['brand']} {car_name}\nVIN: {d['vin']}\n\n회사: {d['company']}\n번호: {d['phone']}\n차량대금: {d['carprice_usd']} USD\n\nUSD 외화\n{d['acc_o']}\n영세율 계산서 거래\n구매확인서 발급\n\n영세율 계산서 금액\n{d['ex_date']} 기준환율 {d['ex_rate']}원\n{d['ex_rate']} * ${d['carprice_usd']} ={d['zerotax']}원"

        elif m_type == "헤이딜러":
            h_type = d['heydlr_type']
            h_id = d['heydlr_id'] if d['heydlr_id'] != "선택 안함" else "ID 미선택"
            msg = "*서북인터내셔널 주식회사*\n\n@@@폐자원매입@@@\n\n"
            msg += f"헤이딜러 {h_type} (사전판매완료 id: {h_id})\n차번호: {plate} // {title_line}\nVIN: {d['vin']}\n"
            if h_type == "일반":
                msg += f"주소: {d['address']}\n번호: {d['phone']}\n\n차량가: {raw_p}\n계좌: {d['acc_o']}\n\n차량번호로 송금 부탁드립니다."
            else:
                msg += f"\n차대금 송금 부탁드립니다~!\n차대금: {raw_p}\n입금계좌:\n{d['acc_o']}\n\n탁송 출발 2시간 전 입금 요망\n일정: {d['heydlr_deliv']}"
            return msg
    return ""

# --- 4. UI 구성 ---
st.set_page_config(layout="wide", page_title="서북인터내셔널 차량 매매 시스템")

# 세션 상태 초기화
for key in ['ex_rate', 'ex_date', 'output_text']:
    if key not in st.session_state: st.session_state[key] = ""

st.markdown("""
    <style>
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton { font-size: 10pt !important; }
    .stButton>button { width: 100%; border-radius: 4px; height: 38px; margin-bottom: 2px; background-color: #f0f2f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    </style>
""", unsafe_allow_html=True)

# [상단] 데이터 입력란
st.subheader("📋 데이터 붙여넣기")
raw_input = st.text_area("엑셀 데이터를 붙여넣으세요", height=70)

parsed = {k: "" for k in IDX.keys()}
if raw_input:
    parts = raw_input.split('\t')
    for key, idx in IDX.items():
        if len(parts) > idx: parsed[key] = parts[idx].strip()
    if len(parsed['vin']) >= 10:
        parsed['year'] = VINYEAR_map.get(parsed['vin'][9].upper(), parsed['year'])
    parsed['color'] = color_map.get(parsed['color'].lower(), parsed['color'].upper())
    for kw, reg in ADDRESS_REGION_MAP.items():
        if kw in parsed['address']: 
            parsed['region'] = reg
            break

# [메인] 35% : 35% : 30% 레이아웃
col_car, col_pay, col_res = st.columns([0.35, 0.35, 0.30])

with col_car:
    st.markdown("### 🚗 차량 정보")
    v_plate = st.text_input("차번호", value=parsed['plate'])
    v_car_name = st.text_input("차명", value=parsed['car_name'])
    v_year = st.text_input("연식", value=parsed['year'])
    v_vin = st.text_input("차대번호(VIN)", value=parsed['vin'])
    v_addr = st.text_input("주소", value=parsed['address'])
    v_phone = st.text_input("딜러연락처", value=parsed['dealer_phone'])
    v_region = st.text_input("지역", value=parsed['region'])
    v_biz_num = st.text_input("사업자번호", value="")

with col_pay:
    st.markdown("### 💰 정산 및 계좌")
    v_price = st.text_input("계산서(O) / 차량대", value=parsed['price'])
    v_contract_x = st.text_input("계산서(X)", value=parsed['contract'])
    v_fee = st.text_input("매도비", value=parsed['fee'])
    v_total = st.text_input("합계금액", value=format_number(parse_money(v_price)+parse_money(v_fee)))
    
    with st.expander("💳 송금 계좌 정보", expanded=True):
        v_acc_o = st.text_input("차량대 계좌", value="")
        v_acc_x = st.text_input("계산서(X) 계좌", value="")
        v_acc_fee = st.text_input("매도비 계좌", value="")
        v_sender = st.text_input("입금자명", value="서북인터")

    with st.expander("🌐 플랫폼 및 환율"):
        v_site = st.text_input("사이트", value=parsed['site'])
        v_sales = st.text_input("세일즈팀", value=parsed['sales'])
        c_ex1, c_ex2 = st.columns([2, 1])
        c_ex1.text_input("현재환율", value=st.session_state['ex_rate'])
        if c_ex2.button("환율조회"): get_exchange_rate(); st.rerun()
        v_deposit = st.text_input("계약금(만원)", value="0")
        v_final_bal = st.text_input("잔금", value=parsed['balance'])

# 데이터 통합 팩 (메시지 함수 전달용)
d = {
    'plate': v_plate, 'year': v_year, 'car_name': v_car_name, 'vin': v_vin,
    'address': v_addr, 'phone': v_phone, 'region': v_region, 'biz_num': v_biz_num,
    'price': v_price, 'fee': v_fee, 'contract_x': v_contract_x, 'total': v_total,
    'acc_o': v_acc_o, 'acc_x': v_acc_x, 'acc_fee': v_acc_fee, 'sender': v_sender,
    'sales': v_sales, 'site': v_site, 'deposit': v_deposit, 'final_bal': v_final_bal,
    'heydlr_type': st.sidebar.selectbox("헤이딜러 타입", ["일반", "제로", "바로낙찰"], index=1),
    'heydlr_id': st.sidebar.text_input("헤이딜러 ID", value="ID 미선택"),
    'heydlr_deliv': parsed['heydlr_delivery'],
    'company': "회사명", 'brand': "브랜드", 'carprice_usd': "0", 
    'ex_date': st.session_state['ex_date'], 'ex_rate': st.session_state['ex_rate'], 'zerotax': "0"
}

with col_res:
    st.markdown("### 📝 리스트 탭")
    t_msg, t_remit, t_etc = st.tabs(["메시지출력", "송금요청", "기타"])
    
    with t_msg:
        m1, m2 = st.columns(2)
        if m1.button("확인후"): st.session_state.output_text = generate_message("확인후", d)
        if m2.button("세일즈팀"): st.session_state.output_text = generate_message("세일즈팀", d)
        m3, m4 = st.columns(2)
        if m3.button("검수자"): st.session_state.output_text = generate_message("검수자", d)
        if m4.button("문자"): st.session_state.output_text = generate_message("문자", d)
        m5, m6 = st.columns(2)
        if m5.button("아웃소싱"): st.session_state.output_text = generate_message("아웃소싱", d)
        if m6.button("주소공유"): st.session_state.output_text = generate_message("주소공유", d)
        if st.button("서류문자"): st.session_state.output_text = generate_message("서류문자", d)

    with t_remit:
        r1, r2 = st.columns(2)
        if r1.button("일반매입"): st.session_state.output_text = generate_message("일반매입", d, "remit")
        if r2.button("폐자원매입"): st.session_state.output_text = generate_message("폐자원매입", d, "remit")
        r3, r4 = st.columns(2)
        if r3.button("계약금"): st.session_state.output_text = generate_message("계약금", d, "remit")
        if r4.button("송금완료"): st.session_state.output_text = generate_message("송금완료", d, "remit")
        r5, r6 = st.columns(2)
        if r5.button("계약금 송금완료"): st.session_state.output_text = generate_message("계약금 송금완료", d, "remit")
        if r6.button("오토위니"): st.session_state.output_text = generate_message("오토위니", d, "remit")
        if st.button("헤이딜러"): st.session_state.output_text = generate_message("헤이딜러", d, "remit")

    with t_etc:
        if st.button("입고방"): st.session_state.output_text = f"입고알림: {v_plate} ({v_car_name})"
        if st.button("사이트 공유"): st.session_state.output_text = f"사이트: {v_site}\n딜러: {v_phone}"

    st.divider()
    st.session_state.output_text = st.text_area("출력 결과", value=st.session_state.output_text, height=300)
    
    b1, b2 = st.columns(2)
    if b1.button("📋 내용복사"): st.toast("Ctrl+C를 눌러 복사하세요")
    if b2.button("♻️ 내용리셋"):
        st.session_state.output_text = ""
        st.rerun()
