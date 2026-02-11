import streamlit as st
import re
from datetime import datetime
import logic as lg
import price_manager as pm
import message as msg_logic
import remit
import etc
import dealerinfo
import country
import mapping
import inventoryenter
import Inspectioncheck

# --- 0. 기본 설정 및 세션 초기화 ---
st.set_page_config(layout="wide", page_title="서북인터내셔널 매매 시스템")

# 페이지 방문 체크 및 자동 리셋
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "buyprogram"
if st.session_state["current_page"] != "buyprogram":
    keys_to_delete = ["dealer_data", "last_searched_phone", "detected_region", "country_data", "last_searched_buyer", "raw_input_main", "inspection_status"]
    for key in keys_to_delete:
        if key in st.session_state: del st.session_state[key]
    st.session_state["current_page"] = "buyprogram"

if "dealer_data" not in st.session_state: st.session_state["dealer_data"] = {}
if "inspection_status" not in st.session_state: st.session_state["inspection_status"] = "X"

# CSS
st.markdown("<style>.stButton>button { width: 100%; margin-bottom: 5px; }</style>", unsafe_allow_html=True)

# --- 1. 상단: 데이터 입력칸 ---
st.subheader("📥 데이터 붙여넣기")
top_col1, top_col2 = st.columns([8, 1])

with top_col2:
    if st.button("♻️ 전체 리셋"):
        keys_to_clear = ["dealer_data", "last_searched_phone", "detected_region", "country_data", "last_searched_buyer", "raw_input_main", "inspection_status", "last_checked_plate"]
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

with top_col1:
    raw_input = st.text_area("엑셀 데이터를 이곳에 붙여넣으세요", height=100, key="raw_input_main")

# 데이터 파싱 및 자동 조회 로직 (raw_input 생성 후 배치)
parsed = {}
if raw_input:
    parsed = lg.parse_excel_data(raw_input)
    
    # 딜러 조회
    contact = parsed.get('dealer_phone', "")
    if contact and st.session_state.get('last_searched_phone') != contact:
        dealer_res = dealerinfo.search_dealer_info(contact)
        if dealer_res["status"] == "success":
            st.session_state["dealer_data"] = dealer_res
            st.session_state["last_searched_phone"] = contact
            
    # Inspection 조회
    plate = parsed.get('plate', "").strip()
    if plate and st.session_state.get('last_checked_plate') != plate:
        insp_status = Inspectioncheck.fetch_inspection_status(plate)
        st.session_state["inspection_status"] = insp_status
        st.session_state["last_checked_plate"] = plate

    # 지역 및 바이어 나라 조회 (기존 로직 유지)
    d_data = st.session_state.get("dealer_data", {})
    final_addr = d_data.get("address") if d_data.get("address") else parsed.get("address", "")
    st.session_state["detected_region"] = mapping.get_region_from_address(final_addr)
    
    buyer_val = parsed.get('buyer', "").strip()
    if buyer_val and st.session_state.get('last_searched_buyer') != buyer_val:
        res = country.handle_buyer_country(buyer_val, "")
        if res["status"] == "fetched":
            st.session_state["country_data"] = res["country"]
            st.session_state["last_searched_buyer"] = buyer_val

st.divider()

# --- 2. 메인 화면 구성 ---
col_info, col_list = st.columns([0.7, 0.3])

with col_info:
    d_data = st.session_state.get("dealer_data", {})
    
    # 타이틀 + Inspection
    title_col, insp_col = st.columns([4, 1])
    title_col.markdown("### 🚗 매입 정보")
    
    insp_list = ["X", "S", "C"]
    current_insp = st.session_state.get("inspection_status", "X")
    insp_idx = insp_list.index(current_insp) if current_insp in insp_list else 0
    v_inspection = insp_col.selectbox("Inspection", insp_list, index=insp_idx, key="v_inspection_key", label_visibility="collapsed")

    # R1~R4 위젯 (기존 코드와 동일하게 배치하되 NameError 방지를 위해 순서 준수)
    r1_1, r1_2, r1_3, r1_4 = st.columns(4)
    v_plate = r1_1.text_input("차번호", value=parsed.get('plate', ""))
    v_year = r1_2.text_input("연식", value=parsed.get('year', ""))
    v_car_name = r1_3.text_input("차명", value=parsed.get('car_name', ""))
    v_car_name_remit = r1_4.text_input("차명(송금용)", value=parsed.get('car_name', ""))

    r2_1, r2_2, r2_3, r2_4 = st.columns(4)
    v_brand = r2_1.text_input("브랜드", value=parsed.get('brand', ""))
    v_vin = r2_2.text_input("VIN", value=parsed.get('vin', ""))
    v_km = r2_3.text_input("km", value=parsed.get('km', ""))
    v_color = r2_4.text_input("color", value=parsed.get('color', ""))

    r3_1, r3_2, r3_3, r3_4, r3_5 = st.columns([1.5, 1.5, 1.5, 1.5, 1])
    v_site = r3_1.text_input("사이트", value=parsed.get('site', ""))
    v_sales = r3_2.text_input("세일즈팀", value=parsed.get('sales', ""))
    v_buyer = r3_3.text_input("바이어", value=parsed.get('buyer', ""))
    v_country = r3_4.text_input("나라", value=st.session_state.get("country_data", ""))
    if r3_5.button("확인", key="btn_country_confirm"):
        res = country.handle_buyer_country(v_buyer, v_country)
        if res["status"] == "fetched": st.session_state["country_data"] = res["country"]; st.rerun()

    r4_1, r4_2, r4_3 = st.columns([1.5, 1.5, 3])
    v_dealer_phone = r4_1.text_input("딜러연락처", value=parsed.get('dealer_phone', ""))
    v_region = r4_2.text_input("지역", value=st.session_state.get("detected_region", parsed.get('region', "")), key="v_region_key")
    v_address = r4_3.text_input("주소", value=d_data.get("address") if d_data.get("address") else parsed.get('address', ""), key="v_address_key")

    with st.container(border=True):
        st.caption("🏢 딜러/판매자 정보")
        biz_c1, biz_c2 = st.columns(2)
        v_biz_name = biz_c1.text_input("상사명", value=d_data.get("company", ""), key="v_biz_name_input")
        v_biz_num = biz_c2.text_input("사업자번호", value=d_data.get("biz_num") if d_data.get("biz_num") else parsed.get('dealer_number', ""), key="v_biz_num_input")

    acc_col1, acc_col2 = st.columns([2, 3])
    v_price = acc_col1.text_input("차량대", value=pm.format_number(parsed.get('price', "")))
    v_acc_o = acc_col2.text_input("차량대 계좌", value=d_data.get("acc_o", ""), key="acc_o_input")
    
    # 계산서X, 매도비 위젯 추가 (생략됨을 방지)
    acc3, acc4 = st.columns([2, 3])
    v_contract_x = acc3.text_input("계산서X", value=pm.format_number(parsed.get('contract', "")))
    v_acc_x = acc4.text_input("계산서X 계좌", value=d_data.get("acc_x", ""), key="acc_x_input")
    acc5, acc6 = st.columns([2, 3])
    v_fee = acc5.text_input("매도비", value=pm.format_number(parsed.get('fee', "")))
    v_acc_fee = acc6.text_input("매도비 계좌", value=d_data.get("acc_fee", ""), key="acc_fee_input")

    total_val = pm.calculate_total(v_price, v_contract_x, v_fee)
    r5_1, r5_2, r5_3 = st.columns([2, 2, 2])
    v_total = r5_1.text_input("합계금액 (자동계산)", value=pm.format_number(total_val), disabled=True)
    v_declaration = r5_2.text_input("DECLARATION", value=pm.format_number(parsed.get('declaration', "0")), key="v_declaration_key")
    v_sender = r5_3.text_input("입금자명", value=d_data.get("sender", "서북인터"), key="sender_input")

    btn_c1, btn_c2 = st.columns(2)
    if btn_c1.button("🏦 계좌확인"):
        res = dealerinfo.search_dealer_info(v_dealer_phone)
        if res["status"] == "success": st.session_state["dealer_data"] = res; st.rerun()
    if btn_c2.button("📝 정보 추가&수정", type="primary"):
        save_data = {"phone": v_dealer_phone, "biz_num": v_biz_num, "biz_name": v_biz_name, "address": v_address, "acc_o": v_acc_o, "acc_fee": v_acc_fee, "sender": v_sender}
        res = dealerinfo.save_or_update_dealer(save_data)
        if res["status"] == "success": st.success(res["message"])

    # 하단 세부 정산 (기존 레이아웃 유지)
    row_bottom = st.columns(2)
    with row_bottom[0]:
        with st.container(border=True):
            v_deposit = st.text_input("계약금(만원)", value="0")
            v_balance = st.text_input("잔금", value=pm.format_number(pm.calculate_balance(v_total, v_deposit)))
        with st.container(border=True):
            v_h_type = st.selectbox("헤이딜러 타입", ["선택", "일반", "제로", "바로낙찰"], index=0)
            v_h_id = st.selectbox("헤이딜러 ID", ["선택", "seobuk", "inter77", "leeks21"], index=0)
            v_h_delivery = st.text_input("헤이딜러 탁송", value=parsed.get('heydlr_delivery', ""))
        with st.container(border=True):
            auc_c1, auc_c2 = st.columns(2)
            v_auc_type = auc_c1.selectbox("옥션 타입", ["선택", "현대", "오토허브", "롯데", "K car"], index=0)
            v_auc_region = auc_c2.text_input("옥션 지역(회차)", value="")

    with row_bottom[1]:
        with st.container(border=True):
            v_company = st.text_input("업체명(오토위니)", value="")
            v_ex_date = st.text_input("환율기준일", value="")
            v_ex_rate = st.text_input("환율", value="")
            v_usd = st.text_input("차량대금($)", value="")
            v_won = st.text_input("영세율금액(원)", value="")

# --- [우측: 리스트탭 (30%)] ---
with col_list:
    st.markdown("### 📋 리스트 탭")
    tab1, tab2, tab3 = st.tabs(["💬 문자전송", "💵 송금요청", "➕ 기타"])

    # 공통 데이터 수집 (모든 탭에서 사용)
    reg_data = {
        "plate": v_plate, "year": v_year, "car_name": v_car_name, "car_name_remit": v_car_name_remit,
        "brand": v_brand, "vin": v_vin, "km": v_km, "color": v_color,
        "region": v_region, "sales": v_sales, "buyer": v_buyer, "country": v_country,
        "inspection": v_inspection, "site": v_site, "dealer_phone": v_dealer_phone,
        "price": v_price, "fee": v_fee, "contract_x": v_contract_x, "total": v_total,
        "deposit": v_deposit, "balance": v_balance, "acc_o": v_acc_o, "acc_x": v_acc_x, "acc_fee": v_acc_fee,
        "biz_name": v_biz_name, "biz_num": v_biz_num, "address": v_address, "sender": v_sender,
        "h_type": v_h_type, "h_id": v_h_id, "h_delivery": v_h_delivery,
        "company": v_company, "ex_date": v_ex_date, "ex_rate": v_ex_rate, "usd_price": v_usd, "won_price": v_won,
        "auc_type": v_auc_type, "auc_region": v_auc_region, "declaration": v_declaration
    }

    with tab1:
        m_c1, m_c2 = st.columns(2)
        if m_c1.button("확인후", key="btn_confirm"): st.session_state["out_tab1_final"] = msg_logic.handle_confirm(reg_data, "confirm"); st.rerun()
        if m_c2.button("세일즈팀", key="btn_sales"): st.session_state["out_tab1_final"] = msg_logic.handle_confirm(reg_data, "salesteam"); st.rerun()
        st.text_area("결과", height=300, key="out_tab1_final")

    with tab2:
        r_c1, r_c2 = st.columns(2)
        if r_c1.button("일반매입 송금"): st.session_state["out_tab2_final"] = remit.handle_remit(reg_data, "일반매입"); st.rerun()
        if r_c2.button("계약금 송금"): st.session_state["out_tab2_final"] = remit.handle_remit(reg_data, "계약금"); st.rerun()
        st.text_area("결과", height=300, key="out_tab2_final")

    with tab3:
        e_c1, e_c2 = st.columns(2)
        if e_c1.button("입고방 알림"): st.session_state["out_tab3_final"] = etc.handle_etc(reg_data, "입고방"); st.rerun()
        if e_c2.button("🚀 정보등록", type="primary"):
            with st.spinner("등록 중..."):
                res = inventoryenter.run_integrated_registration(reg_data)
                if res["status"] in ["success", "partial"]: st.success(res["message"])
                else: st.error(res["message"])
        if e_c1.button("서류안내 문자"): st.session_state["out_tab3_final"] = etc.handle_etc(reg_data, "서류문자"); st.rerun()
        if v_site and v_site.startswith("http"): st.link_button("🌐 사이트 이동", v_site)
        st.text_area("결과", height=300, key="out_tab3_final")
