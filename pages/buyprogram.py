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
import socket
import google_sheet_manager as gsm

# --- 0. 모든 위젯 키 정의 (항상 최상단에 위치) ---
ALL_WIDGET_KEYS = [
    "raw_input_main", "v_region_key", "v_address_key", 
    "v_biz_name_input", "v_biz_num_input", "acc_o_input", 
    "acc_x_input", "acc_fee_input", "sender_input", 
    "v_declaration_key", "v_inspection_key", "auto_alt_car_name"
]

# --- 1. 페이지 상태 및 리셋 로직 ---
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "buyprogram"

if st.session_state["current_page"] != "buyprogram":
    for k in ALL_WIDGET_KEYS:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state["dealer_data"] = {}
    st.session_state["detected_region"] = ""
    st.session_state["country_data"] = ""
    st.session_state["inspection_status"] = "X"
    st.session_state["current_page"] = "buyprogram"
    st.rerun()

# --- 2. 기본 페이지 설정 ---
st.set_page_config(layout="wide", page_title="서북인터내셔널 매매 시스템")

# 전체 입력 및 출력칸 시각화 최적화
st.markdown("""
    <style>
    /* 1. 기본 설정: 모든 입력창 및 텍스트 영역 글자색 검정 고정 */
    input, textarea, select, .stSelectbox div {
        color: #000000 !important;
        font-weight: 500 !important;
    }

    /* 2. 버튼 스타일 (전체 동일) */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        background-color: #f0f2f6; 
        color: #000000 !important;
        border: 1px solid #d1d5db;
    }
    
    /* 1. 선택박스 전체 영역 (배경을 흰색으로) */
    div[data-testid="stSelectbox"] > div {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    /* 2. 선택박스 내부의 글자색 (검정 고정) */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* 3. 드롭다운 화살표 아이콘 색상 (검정) */
    div[data-testid="stSelectbox"] svg {
        fill: #000000 !important;
    }

    /* 4. 클릭 시 나타나는 드롭다운 목록(Pop-over) 글자색 보정 */
    div[data-baseweb="popover"] ul {
        background-color: #FFFFFF !important;
    }
    
    div[data-baseweb="popover"] li {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }

    /* 3. 차량 기본 정보 (연한 회색) - 차번호, 연식, 브랜드 등 */
    input[aria-label="차번호"], input[aria-label="연식"], input[aria-label="차명"], 
    input[aria-label="브랜드"], input[aria-label="VIN"], input[aria-label="km"], 
    input[aria-label="color"] {
        background-color: #F9FAFB !important;
        border: 1px solid #D1D5DB !important;
    }

    /* 4. 업무 및 바이어 정보 (연한 보라) - 사이트, 세일즈, 바이어, 나라 */
    input[aria-label="사이트"], input[aria-label="세일즈팀"], 
    input[aria-label="바이어"], input[aria-label="나라"] {
        background-color: #F5F3FF !important;
        border: 1px solid #DDD6FE !important;
    }

    /* 5. 연락처 및 주소 정보 (연한 녹색) - 연락처, 지역, 주소 */
    input[aria-label="딜러연락처"], input[aria-label="지역"], input[aria-label="주소"] {
        background-color: #F0FDF4 !important;
        border: 1px solid #BBF7D0 !important;
    }

    /* 6. 핵심 상사 및 계좌 정보 (연한 노랑) - 상사명, 사업자번호, 계좌들 */
    input[aria-label="상사명"], input[aria-label="사업자번호"], 
    input[aria-label="차량대"], input[aria-label="계산서X"], input[aria-label="매도비"],
    input[aria-label="차량대 계좌"], input[aria-label="계산서X 계좌"], input[aria-label="매도비 계좌"] {
        background-color: #FEFCE8 !important;
        border: 1px solid #FEF08A !important;
        font-weight: bold !important;
    }

    /* 7. 시스템 자동계산 및 중요 행정 (연한 주황) - 합계금액, 잔금, DECLARATION, 입금자명, 송금용차명 */
    input[aria-label="합계금액 (자동계산)"], input[aria-label="잔금"], input[aria-label="계약금(만원 단위)"],
    input[aria-label="DECLARATION"], input[aria-label="입금자명"], 
    input[aria-label="차명(송금용)"] {
        background-color: #FFF7ED !important;
        border: 1px solid #FFEDD5 !important;
    }

    /* 2. 오토위니 및 수출 정보 (연한 청록) - 구분하기 쉽게 색상 추가 */
    input[aria-label="업체명"], 
    input[aria-label="환율기준일"], 
    input[aria-label="환율"], 
    input[aria-label="차량대금($)"], 
    input[aria-label="영세율금액(원)"] {
        background-color: #ECFEFF !important; /* Light Cyan */
        border: 1px solid #CFFAFE !important;
    }

    /* 7. 헤이딜러 및 경매 정보 (연한 핑크) - 추가 구분 */
    input[aria-label="헤이딜러 탁송"], 
    input[aria-label="옥션 지역(회차)"] {
        background-color: #FFF1F2 !important;
        border: 1px solid #FFE4E6 !important;
    }

    /* 8. 출력칸 스타일 (연한 하늘색) - 문자 출력 결과, 송금 요청 결과 등 */
    textarea {
        background-color: #F0F9FF !important;
        color: #000000 !important;
        border: 1px solid #BAE6FD !important;
        font-family: 'Malgun Gothic', sans-serif !important;
        font-size: 15px !important;
    }

    /* 10. 탭(Tab) 글자색 보정 */
    button[data-baseweb="tab"] div p {
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'output_text' not in st.session_state:
    st.session_state.output_text = ""

label_col, delete_col = st.columns([7, 1])

with label_col:
    st.subheader("📥 데이터 붙여넣기")

with delete_col:
    # 입력칸만 비우는 전용 버튼
    if st.button("🗑️ 입력 삭제"):
        if "raw_input_main" in st.session_state:
            st.session_state["raw_input_main"] = ""  # 값을 직접 빈 문자열로 강제 주입
        st.session_state["last_raw_input"] = ""      # 비교용 데이터도 초기화
        st.session_state["parsed_data"] = {}         # 파싱된 바구니도 비움
        st.rerun()
raw_input = st.text_area("엑셀 데이터를 이곳에 붙여넣으세요", height=100, key="raw_input_main")

# [핵심 수정] parsed 데이터를 세션에서 관리합니다.
if "parsed_data" not in st.session_state:
    st.session_state["parsed_data"] = {}

if raw_input:
    # 이전에 처리했던 입력값과 현재 입력값이 다를 때만 파싱 실행
    if st.session_state.get("last_raw_input") != raw_input:
        with st.spinner("데이터 파싱 및 조회 중..."):
            parsed = lg.parse_excel_data(raw_input)
            
            # 1. Inspection 조회
            plate = parsed.get('plate', "").strip()
            if plate:
                res_status = Inspectioncheck.fetch_inspection_status(plate)
                st.session_state["inspection_status"] = res_status
                # [추가] 셀렉트박스 위젯 키 강제 동기화
                st.session_state["v_inspection_key"] = res_status

            # 2. 딜러 정보 조회
            contact = parsed.get('dealer_phone', "")
            if contact:
                dealer_res = dealerinfo.search_dealer_info(contact)
                if dealer_res["status"] == "success":
                    st.session_state["dealer_data"] = dealer_res
                    # --- 위젯 키에 직접 할당하여 화면 즉시 반영 ---
                    st.session_state["v_address_key"] = dealer_res.get("address", "")
                    st.session_state["v_biz_name_input"] = dealer_res.get("company", "")
                    st.session_state["v_biz_num_input"] = dealer_res.get("biz_num", "")
                    st.session_state["acc_o_input"] = dealer_res.get("acc_o", "")
                    st.session_state["acc_fee_input"] = dealer_res.get("acc_fee", "")
                    st.session_state["sender_input"] = dealer_res.get("sender", "")
                else:
                    st.session_state["dealer_data"] = {}

            # 3. 바이어 국가 조회
            buyer = parsed.get('buyer', "").strip()
            if buyer:
                res = country.handle_buyer_country(buyer, "")
                if res["status"] == "fetched":
                    st.session_state["country_data"] = res["country"]

            # [추가] 차명 매핑 및 송금용 차명 결정
            import google_sheet_manager as gsm
            car_map = gsm.get_car_name_map()
            original_car_name = parsed.get('car_name', "")
            alt_name = lg.get_alt_car_name(original_car_name, car_map)
            st.session_state["auto_alt_car_name"] = alt_name # 세션에 저장
            
            # [추가] 주소에서 지역 추출 로직
            parsed_address = parsed.get('address', "")
            detected = mapping.get_region_from_address(parsed_address)
            st.session_state["detected_region"] = detected  # 찾은 지역 저장

            # 마무리 상태 저장 및 리런
            st.session_state["last_raw_input"] = raw_input
            st.session_state["parsed_data"] = parsed
            st.rerun()

# 현재 화면에서 사용할 parsed 데이터 로드
parsed = st.session_state.get("parsed_data", {})
    
# 리셋 버튼을 위해 컬럼 나눔
top_col1, top_col2 = st.columns([8, 1])

top_col1, top_col2 = st.columns([8, 1])
with top_col2:
    if st.button("♻️ 전체 리셋"):
        for k in ALL_WIDGET_KEYS:
            if k in st.session_state: del st.session_state[k]
        st.session_state["last_raw_input"] = ""
        st.session_state["parsed_data"] = {}
        st.session_state["dealer_data"] = {}
        st.rerun()

if "inspection_status" not in st.session_state:
    st.session_state["inspection_status"] = "X"
st.divider()
        
# --- 2. 메인 화면 구성 (70% : 30%) ---
col_info, col_list = st.columns([0.7, 0.3])

# --- [좌측: 매입정보 (70%)] ---
with col_info:
    d_data = st.session_state.get("dealer_data", {})
    title_col, insp_col = st.columns([4, 1])
    with title_col:
        st.markdown("### 🚗 매입 정보")
    with insp_col:
        # 상태값 인덱스 계산 로직을 여기로 옮겨오면 더 좋습니다.
        insp_list = ["X", "S", "C"]
        current_insp = st.session_state.get("inspection_status", "X")
        try:
            insp_idx = insp_list.index(current_insp)
        except:
            insp_idx = 0

        v_inspection = st.selectbox(
            "Inspection", 
            insp_list, 
            index=insp_idx, 
            key="v_inspection_key", # 유일한 키 유지
            label_visibility="collapsed"
        )

   
    # R1: 차번호, 연식, 차명, 차명(송금용)
    r1_1, r1_2, r1_3, r1_4 = st.columns(4)
    v_plate = r1_1.text_input("차번호", value=parsed.get('plate', ""))
    v_year = r1_2.text_input("연식", value=parsed.get('year', ""))
    v_car_name = r1_3.text_input("차명", value=parsed.get('car_name', ""))
    default_alt_name = st.session_state.get("auto_alt_car_name", v_car_name)
    v_car_name_remit = r1_4.text_input("차명(송금용)", value=default_alt_name)

    # R2: 브랜드, VIN, km, color
    r2_1, r2_2, r2_3, r2_4 = st.columns(4)
    v_brand = r2_1.text_input("브랜드", value=parsed.get('brand', ""))
    v_vin = r2_2.text_input("VIN", value=parsed.get('vin', ""))
    v_km = r2_3.text_input("km", value=parsed.get('km', ""))
    v_color = r2_4.text_input("color", value=parsed.get('color', ""))

    # R3: 사이트, 세일즈팀, 바이어, 나라, 확인버튼
    r3_1, r3_2, r3_3, r3_4, r3_5 = st.columns([1.5, 1.5, 1.5, 1.5, 1])
    v_site = r3_1.text_input("사이트", value=parsed.get('site', ""))
    v_sales = r3_2.text_input("세일즈팀", value=parsed.get('sales', ""))
    v_buyer = r3_3.text_input("바이어", value=parsed.get('buyer', ""))
    
    # 세션에 저장된 나라 정보가 있으면 그걸 먼저 보여줌
    current_country_val = st.session_state.get("country_data", "")
    v_country = r3_4.text_input("나라", value=current_country_val if current_country_val else "")

    if r3_5.button("확인", key="btn_country_confirm"):
        with st.spinner("데이터 처리 중..."):
            res = country.handle_buyer_country(v_buyer, v_country)
            
            if res["status"] == "fetched":
                st.session_state["country_data"] = res["country"]
                st.success(f"조회 완료: {res['country']}")
                st.rerun()
            elif res["status"] == "updated":
                st.success(f"정보 수정 완료: {v_country}")
            elif res["status"] == "added":
                st.success(f"새로운 바이어 추가 완료: {v_buyer}")
            elif res["status"] == "match":
                st.info("정보가 이미 일치합니다.")
            else:
                st.error(res.get("message", "오류가 발생했습니다."))
    # R4: 연락처, 지역, 주소
    r4_1, r4_2, r4_3 = st.columns([1.5, 1.5, 3])
    v_dealer_phone = r4_1.text_input("딜러연락처", value=parsed.get('dealer_phone', ""))
    # dealer_data가 딕셔너리인지 한 번 더 확인하는 안전 장치
    d_data = st.session_state.get("dealer_data")
    if not isinstance(d_data, dict):
        d_data = {}
    
    # 주소 결정 (구글 시트 우선 -> 없으면 엑셀 파싱 데이터)
    sheet_address = d_data.get("address", "")
    parsed_address = parsed.get('address', "")
    final_address = sheet_address if sheet_address else parsed_address
    # 주소 (구글 시트 우선)
    v_address = r4_3.text_input(
    "주소", 
    value=final_address,
    key="v_address_key"
    )
    # [수정] 주소가 변경되었을 때 실시간으로 지역을 다시 추출
    if v_address:
        new_detected = mapping.get_region_from_address(v_address)
        if new_detected:
            st.session_state["detected_region"] = new_detected
    
    # [결과] 지역 입력창
    v_region = r4_2.text_input(
        "지역", 
        value=st.session_state.get("detected_region", ""), 
        key="v_region_key"
    )

    # 딜러/판매자 정보 프레임
    with st.container(border=True):
        st.caption("🏢 딜러/판매자 정보")
        biz_c1, biz_c2 = st.columns(2) # 2개 컬럼 생성
        v_biz_name = biz_c1.text_input("상사명", value=d_data.get("company", ""), key="v_biz_name_input")
        # 변수명을 v_biz_num으로 통일하여 NameError 방지
        v_biz_num = biz_c2.text_input(
            "사업자번호", 
            value=d_data.get("biz_num") if d_data.get("biz_num") else parsed.get('dealer_number', ""),
            key="v_biz_num_input"
        )

    # 계좌 정보 섹션
    acc1, acc2 = st.columns([2, 3])
    # 엑셀에서 가져온 원본 숫자를 "1,300만원" 형식으로 변환하여 표시
    v_price = acc1.text_input("차량대", value=pm.format_number(parsed.get('price', "")))
    # 2. DECLARATION 자동 계산 로직 적용
    # 엑셀에서 가져온 값이 있으면 그것을 쓰고, 없으면 차량대금 기반으로 자동 계산
    excel_decl = parsed.get('declaration', "0")
    if excel_decl and excel_decl != "0":
        auto_decl_val = pm.parse_money(excel_decl)
    else:
        auto_decl_val = pm.calculate_declaration(v_price)
    v_acc_o = acc2.text_input("차량대 계좌", value=d_data.get("acc_o", ""), key="acc_o_input")

    acc3, acc4 = st.columns([2, 3])
    v_contract_x = acc3.text_input("계산서X", value=pm.format_number(parsed.get('contract', "")))
    v_acc_x = acc4.text_input("계산서X 계좌", value=d_data.get("acc_x", ""))

    acc5, acc6 = st.columns([2, 3])
    v_fee = acc5.text_input("매도비", value=pm.format_number(parsed.get('fee', "")))
    v_acc_fee = acc6.text_input("매도비 계좌", value=d_data.get("acc_fee", ""))

        # 입력창에 써있는 글자들을 숫자로 바꿔서 더함
    total_val = pm.calculate_total(v_price, v_contract_x, v_fee)
    # 3. 합계금액 입력창을 만듭니다. (이때 v_total 변수가 생성됨)
    r5_1, r5_2, r5_3 = st.columns([2, 2, 2])
    
    v_total = r5_1.text_input("합계금액 (자동계산)", value=pm.format_number(total_val), disabled=True)
    
    v_declaration = r5_2.text_input(
    "DECLARATION", 
    value=pm.format_number(auto_decl_val), # 계산된 값을 포맷팅해서 표시
    key="v_declaration_key"
    )
    
    v_sender = r5_3.text_input(
        "입금자명", 
        value=d_data.get("sender", ""), 
        key="sender_input"
    )
    
    
    # 🏦 계좌확인 버튼 클릭 시
    if r5_2.button("🏦 계좌확인"):
        with st.spinner("구글 시트에서 정보를 불러오는 중..."):
            result = dealerinfo.search_dealer_info(v_dealer_phone)
            
            if result["status"] == "success":
                # 찾은 정보들을 세션 상태나 위젯의 기본값에 반영하기 위해 rerun 혹은 직접 할당
                # 여기서는 가장 간단하게 toast로 알리고 필드 값을 업데이트하는 로직이 필요합니다.
                # (Streamlit은 rerun 없이 위젯 값을 바꾸기 어려우므로, 결과값을 session_state에 담아 활용하는 것을 권장합니다.)
                st.session_state["dealer_data"] = result
                st.success(f"정보 조회 성공: {result['company']}")
                st.rerun() # 업데이트된 값을 화면에 보여주기 위해 재실행
            
            elif result["status"] == "empty":
                st.warning(result["message"])
            else:
                st.error(result["message"])
    if r5_3.button("📝 정보 추가&수정", type="primary"):
    # 아래 딕셔너리의 키 이름들을 dealerinfo.py의 data.get() 이름과 맞춥니다.
        current_data = {
            "phone": v_dealer_phone,     # dealerinfo에서는 'phone'으로 찾음
            "biz_num": v_biz_num,       # 'biz_num'
            "biz_name": v_biz_name,     # 'biz_name' (상사명)
            "address": v_address,       # 'address'
            "acc_o": v_acc_o,           # 'acc_o'
            "acc_fee": v_acc_fee,       # 'acc_fee'
            "sender": v_sender          # 'sender'
        }
    
        with st.spinner("구글 시트 업데이트 중..."):
            save_res = dealerinfo.save_or_update_dealer(current_data)
            
            if save_res["status"] == "success":
                st.success(save_res["message"])
                # 저장 성공 후 화면의 데이터를 최신으로 유지하기 위해 세션 업데이트
                st.session_state["dealer_data"] = {
                    "biz_num": v_biz_num,
                    "company": v_biz_name,
                    "address": v_address,
                    "acc_o": v_acc_o,
                    "acc_fee": v_acc_fee,
                    "sender": v_sender
                }
                # st.rerun()  # 필요시 화면 새로고침
            else:
                st.error(save_res["message"])

    # 하단 세부 정산 프레임
    row_bottom = st.columns(2)
    with row_bottom[0]:
        # 첫 번째 프레임: 세부정산
        with st.container(border=True):
            st.caption("💰 세부정산")
            v_deposit = st.text_input("계약금(만원 단위)", value="0")
            
            # 실시간 잔금 계산 로직
            balance_val = pm.calculate_balance(v_total, v_deposit)
            v_balance = st.text_input("잔금", value=pm.format_number(balance_val))
            
            # 계약금 확인용 안내 (import re 필요)
            st.write(f"ℹ️ 적용된 계약금: {pm.format_number(pm.get_clean_deposit(v_deposit))}")
        
        with st.container(border=True):
            st.caption("📱 헤이딜러 정보")
            # selectbox는 value 대신 index를 맞춰야 하므로 간단히 기본값 설정
            v_h_type = st.selectbox("헤이딜러 타입", ["선택", "일반", "제로", "바로낙찰"], index=0)
            v_h_id = st.selectbox("헤이딜러 ID", ["선택", "seobuk", "inter77", "leeks21"], index=0)
            v_h_delivery = st.text_input("헤이딜러 탁송", value=parsed.get('heydlr_delivery', ""))
    with row_bottom[0]: # 기존 헤이딜러 정보 container 아래에 추가하거나 새로 생성
            with st.container(border=True):
                st.caption("🔨 경매(옥션) 정보")
                auc_c1, auc_c2 = st.columns(2)
                v_auc_type = auc_c1.selectbox("옥션 타입", ["선택", "현대글로비스", "오토허브", "롯데", "K car"], index=0)
                v_auc_region = auc_c2.text_input("옥션 지역(회차)", value="")

    with row_bottom[1]:
        with st.container(border=True):
            st.caption("🌐 오토위니 (수출)")
            v_company = st.text_input("업체명", value="")
            c_ex1, c_ex2, c_ex3 = st.columns([2, 2, 1])
            v_ex_date = c_ex1.text_input("환율기준일", value="")
            v_ex_rate = c_ex2.text_input("환율", value="")
            if c_ex3.button("조회"): 
                # 여기서 lg.get_exchange_rate() 연동 가능
                pass
            
            v_usd = st.text_input("차량대금($)", value="")
            v_won = st.text_input("영세율금액(원)", value="")

# --- [우측: 리스트탭 (30%)] ---
with col_list:
    st.markdown("### 📋 리스트 탭")
    tab1, tab2, tab3 = st.tabs(["💬 문자전송", "💵 송금요청", "➕ 기타"])

    with tab1:
        input_data = {
            "year": v_year, "car_name": v_car_name, "plate": v_plate,
            "price": v_price, "fee": v_fee, "contract_x": v_contract_x,
            "sales": v_sales, "address": v_address, "dealer_phone": v_dealer_phone,
            "region": v_region, "site": v_site
        }

        m_c1, m_c2 = st.columns(2)
        
        if m_c1.button("확인후", key="btn_confirm"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "confirm")
            st.rerun()
            
        if m_c2.button("세일즈팀", key="btn_sales"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "salesteam")
            st.rerun()

        if m_c1.button("검수자", key="btn_insp"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "inspection")
            st.rerun()

        if m_c2.button("문자", key="btn_sms"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "sms")
            st.rerun()

        if m_c1.button("아웃소싱", key="btn_out"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "outsource")
            st.rerun()

        if m_c2.button("주소공유", key="btn_share"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "share_address")
            st.rerun()

        st.divider()

        # 3. 출력 창 및 유틸리티 버튼
        st.text_area("문자 출력 결과", height=400, key="out_tab1_final")
        content1 = st.session_state.get("out_tab1", "")
        if content1:
            st.caption("👇 우측 상단 복사 아이콘 클릭")
            st.code(content1, language=None)

        if st.button("♻️ 내용리셋", key="rs1"):
            st.session_state["out_tab1"] = ""
            st.rerun()
            
    with tab2:
    # 데이터 수집 (입력창 변수들)
        remit_data = {
            "plate": v_plate, "year": v_year, "car_name": v_car_name, "vin": v_vin,
            "address": v_address, "dealer_phone": v_dealer_phone,
            "price_acc": v_acc_o, "notbill_acc": v_acc_x, "fee_acc": v_acc_fee,
            "sender_name": v_sender, "brand": v_brand, "dealer_number": v_biz_num,
            "price": v_price, "fee": v_fee, "contract_x": v_contract_x,
            "total": v_total, "deposit": v_deposit, "balance": v_balance,
            "company": v_company, "ex_date": v_ex_date, "ex_rate": v_ex_rate,
            "usd_price": v_usd, "won_price": v_won,
            "h_type": v_h_type, "h_id": v_h_id, "h_delivery": v_h_delivery
        }

        r_c1, r_c2 = st.columns(2)
        if r_c1.button("일반매입 송금"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "일반매입")
            st.rerun()
        if r_c2.button("계약금 송금"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "계약금")
            st.rerun()
        if r_c1.button("폐자원 송금"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "폐자원매입")
            st.rerun()
        if r_c2.button("송금완료 확인"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "송금완료")
            st.rerun()
        if r_c1.button("오토위니 송금"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "오토위니")
            st.rerun()
        if r_c2.button("헤이딜러 송금"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "헤이딜러")
            st.rerun()
    
        st.text_area("송금 요청 결과", height=600, key="out_tab2_final")
        content2 = st.session_state.get("out_tab2", "")
        if content2:
            st.caption("👇 우측 상단 복사 아이콘 클릭")
            st.code(content2, language=None)

        if st.button("♻️ 내용리셋", key="rs2"):
            st.session_state["out_tab2"] = ""
            st.rerun()

    with tab3:
        # 데이터 수집 (필요한 모든 위젯 변수 포함)
        ect_data = {
            "plate": v_plate, "year": v_year, "car_name_remit": v_car_name_remit,
            "brand": v_brand, "vin": v_vin, "km": v_km, "color": v_color,
            "region": v_region, "sales": v_sales, "buyer": v_buyer, 
            "country": v_country, "inspection": st.session_state.get("v_inspection_key", "?"),
            "h_type": v_h_type, "h_id": v_h_id, "h_delivery": v_h_delivery,
            "price": v_price, "fee": v_fee, "contract_x": v_contract_x, 
            "deposit": v_deposit, "company": v_company, # 오토위니 업체명
            "biz_name": v_biz_name, "biz_num": v_biz_num,
            "declaration": v_declaration, "ex_rate": v_ex_rate
        }
        e_c1, e_c2 = st.columns(2)
        if e_c1.button("입고방 알림", key="btn_etc1"):
            st.session_state["out_tab3"] = etc.handle_etc(etc_data, "입고방")
            st.rerun()
            
        if e_c2.button("🚀 정보등록", type="primary"):
            with st.spinner("시트에 등록 중..."):
                res = inventoryenter.run_integrated_registration(ect_data)
                if res["status"] in ["success", "partial"]:
                    st.success(res["message"])
                else:
                    st.error(res["message"])
        if e_c2.button("서류안내 문자", key="btn_etc2"):
            st.session_state["out_tab3"] = etc.handle_etc(etc_data, "서류문자")
            st.rerun()
            
        # tab3 내부
        # tab3 내부 또는 등록 버튼 로직 위치
        if st.button("📊 이카운트 품목 최종 등록", key="btn_ecount_real_final"):
            vin_to_check = ect_data.get("vin")
            
            if not vin_to_check:
                st.error("VIN(차대번호) 정보가 없습니다.")
            else:
                with st.spinner("구글 시트에서 차량 정보를 확인 중..."):
                    import inventoryenter
                    import importlib
                    importlib.reload(inventoryenter) # 수정된 함수를 인식하도록 리로드
                    
                    # 이제 AttributeError가 발생하지 않습니다.
                    existing_no = inventoryenter.get_no_by_vin(vin_to_check)
                    
                    if existing_no:
                        st.info(f"확인됨: 구글 시트 순번 NO.{existing_no}")
                        
                        session_id = ecount.get_session_id()
                        if session_id:
                            item_res = ecount.register_item(ect_data, session_id, existing_no)
                            
                            if str(item_res.get("Status")) == "200":
                                st.success(f"✅ 이카운트 동기화 완료! (순번: {existing_no})")
                                st.balloons()
                            else:
                                st.error(f"❌ 이카운트 등록 실패: {item_res.get('Message')}")
                        else:
                            st.error("❌ 이카운트 세션 획득 실패")
                    else:
                        # 구글에 VIN이 없는 경우
                        st.warning("⚠️ 구글에 먼저 등록해주세요. (시트에서 해당 VIN을 찾을 수 없습니다.)")
                    
        # 사이트 이동 버튼 (방법 1 적용)
        if v_site and v_site.startswith("http"):
            e_c2.link_button("🌐 사이트 이동", v_site)
        else:
            e_c2.button("🌐 사이트 이동", disabled=True)

        st.text_area("기타 메시지 결과", height=400, key="out_tab3")       
        content3 = st.session_state.get("out_tab3", "")
        if content3:
            st.caption("👇 우측 상단 복사 아이콘 클릭")
            st.code(content3, language=None)

        if st.button("♻️ 내용리셋", key="rs3"):
            st.session_state["out_tab3"] = ""
            st.rerun()
