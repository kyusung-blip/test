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
import importlib
import inventoryenter
import Inspectioncheck
import socket
import ecount
import google_sheet_manager as gsm
from st_copy_to_clipboard import st_copy_to_clipboard
import cyberts_crawler

# --- 0. 모든 위젯 키 정의 (항상 최상단에 위치) ---
ALL_WIDGET_KEYS = [
    "raw_input_main", "v_region_key", "v_address_key", 
    "v_biz_name_input", "v_biz_num_input", "acc_o_input", 
    "acc_x_input", "acc_fee_input", "sender_input", 
    "v_declaration_key", "v_inspection_key", "auto_alt_car_name",
    "v_psource", "v_spec_num_key"
]

# --- 1. 페이지 상태 및 리셋 로직 ---
if "widget_version" not in st.session_state:
    st.session_state["widget_version"] = 0
    
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "buyprogram"
    st.session_state["out_tab1_final"] = "" # Tab1 결과값 초기화
    st.session_state["out_tab2_final"] = "" # Tab2 결과값 초기화
    st.session_state["out_tab3"] = ""       # Tab3 결과값 초기화
    st.session_state["v_inspection_key"] = "X" # 기본값 설정
    st.session_state["v_psource"] = "" # 기본값 설정
    

if st.session_state["current_page"] != "buyprogram":
    for k in ALL_WIDGET_KEYS:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state["dealer_data"] = {}
    st.session_state["detected_region"] = ""
    st.session_state["country_data"] = ""
    st.session_state["inspection_status"] = "X"
    st.session_state["current_page"] = "buyprogram"
    st.session_state["v_psource"] = "" 
    st.rerun()

# --- 2. 기본 페이지 설정 ---
st.set_page_config(layout="wide", page_title="서북인터내셔널 매매 시스템")

# --- 1-1. 콜백 함수 정의 (주소 변경 시 지역 자동 추출) ---
def update_region():
    address_val = st.session_state.get("v_address_key", "")
    if address_val:
        # mapping 모듈을 사용하여 지역 추출
        detected = mapping.get_region_from_address(address_val)
        # 지역 위젯의 키값에 직접 저장
        st.session_state["v_region_key"] = detected

# 전체 입력 및 출력칸 시각화 최적화
st.markdown("""
    <style>
        /* ===== 배경색 설정 ===== */
    .stApp {
        background-color: #2b2b2b !important;
    }
    
    .main {
        background-color: #2b2b2b !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #2b2b2b !important;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(43, 43, 43, 0.95) !important;
    }
        /* ===== 텍스트 색상 조정 (배경이 어두워졌으므로) ===== */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label {
        color: #FFFFFF !important;
    }
        /* 버튼 텍스트는 검정색으로 재정의 */
    .stButton>button, .stButton>button *, button[data-baseweb="tab"] {
        color: #000000 !important;
    }

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
    
    
    /* 1. 인스펙션 드롭다운(Selectbox) 본체 보정 */
    div[data-testid="stSelectbox"] > div {
        background-color: #FFFFFF !important; /* 배경 흰색 고정 */
        border: 2px solid #EF4444 !important; /* 빨간색 테두리 강조 */
        border-radius: 8px !important;
        color: #000000 !important;
    }

    /* 2. 선택된 후 표시되는 텍스트(Value) 색상 및 배경 */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; /* 내부 배경 흰색 */
        color: #000000 !important; /* 글자색 검정 */
        font-weight: bold !important;
    }
    
    /* 3. 선택박스 내부의 텍스트가 들어가는 실제 span 태그 제어 */
    div[data-testid="stSelectbox"] span {
        color: #000000 !important;
    }

    /* 3. 차량 기본 정보 (연한 회색) - 차번호, 연식, 브랜드 등 */
    input[aria-label="차번호"], input[aria-label="연식"], input[aria-label="차명"], 
    input[aria-label="브랜드"], input[aria-label="VIN"], input[aria-label="km"], 
    input[aria-label="color"] {
        background-color: #F9FAFB !important;
        border: 1px solid #D1D5DB !important;
    }

    /* 4. 업무 및 바이어 정보 (연한 보라) - 사이트, 세일즈, 바이어, 나라, 제원관리번호 */
    input[aria-label="사이트"], input[aria-label="세일즈팀"], 
    input[aria-label="바이어"], input[aria-label="나라"],
    input[aria-label="제원관리번호"] {
        background-color: #F5F3FF !important;
        border: 1px solid #DDD6FE !important;
    }

    /* 5. 연락처 및 주소 정보 (연한 녹색) - 연락처, 지역, 주소 */
    input[aria-label="딜러연락처(phone)"], input[aria-label="지역"], input[aria-label="주소(address)"] {
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

    /* 7. 시스템 자동계산 및 중요 행정 (연한 주황) */
    /* :disabled 설정을 추가하여 합계금액이 계산된 후에도 검정글씨를 유지합니다. */
    input[aria-label="합계금액 (자동계산)"]:disabled,
    input[aria-label="합계금액 (자동계산)"], 
    input[aria-label="잔금"], 
    input[aria-label="계약금(만원 단위)"],
    input[aria-label="DECLARATION"], 
    input[aria-label="입금자명"], 
    input[aria-label="P.Source"],
    input[aria-label="차명(송금용)"] {
        background-color: #FFF7ED !important;
        border: 1px solid #FFEDD5 !important;
        color: #000000 !important; /* 글자색 검정 고정 */
        -webkit-text-fill-color: #000000 !important; /* Safari/Chrome 비활성 글자색 강제 */
        opacity: 1 !important; /* 비활성 시 흐려지는 현상 방지 */
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

label_col, reset_col = st.columns([7, 1])

with label_col:
    st.subheader("📥 데이터 붙여넣기")

with reset_col:
    # 기존 "입력 삭제"와 "전체 리셋" 기능을 통합한 버튼
    if st.button("♻️ 전체 리셋", type="secondary", use_container_width=True):
        # 1. 모든 세션 상태 변수 삭제
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # 2. 필수 기본값 재설정 (오류 방지)
        st.session_state["current_page"] = "buyprogram"
        st.session_state["inspection_status"] = "X"
        st.session_state["v_inspection_key"] = "X"
        st.session_state["parsed_data"] = {}
        st.session_state["dealer_data"] = {}
        st.session_state["country_data"] = ""
        st.session_state["detected_region"] = ""
        
        # 3. 입력창 및 결과값 초기화
        st.session_state["raw_input_main"] = ""
        st.session_state["last_raw_input"] = ""
        st.session_state["out_tab1_final"] = ""
        st.session_state["out_tab2_final"] = ""
        st.session_state["out_tab3"] = ""
        
        # 4. 모든 위젯 키 강제 초기화
        for k in ALL_WIDGET_KEYS:
            st.session_state[k] = ""
            
        # 5. 페이지 새로고침
        st.rerun()
raw_input = st.text_area("엑셀 데이터를 이곳에 붙여넣으세요", height=100, key="raw_input_main")
parsed = st.session_state.get("parsed_data", {})

# --- 1. 파싱 및 외부 데이터 조회 로직 (위젯 선언보다 상단에 위치) ---
if raw_input:
    # 중복 실행 방지: 이전 입력값과 다를 때만 실행
    if st.session_state.get("last_raw_input") != raw_input:
        with st.spinner("데이터를 분석하고 외부 정보를 조회 중입니다..."):
            # A. 기초 데이터 파싱 (logic.py)
            parsed_result = lg.parse_excel_data(raw_input)
            # [수정] 위젯이 그려지기 전에 세션 값을 먼저 세팅합니다.
            st.session_state["v_spec_num_key"] = parsed_result.get('spec_num', "")
                       
            # B. 주요 변수 추출
            plate = parsed_result.get('plate', "").strip()
            contact = parsed_result.get('dealer_phone', "").strip()
            buyer = parsed_result.get('buyer', "").strip()
            original_car_name = parsed_result.get('car_name', "")
            parsed_address = parsed_result.get('address', "")
            
            # 1️⃣ [P.Source 세션 저장]
            st.session_state["v_psource"] = parsed_result.get('psource', "")
            st.session_state["v_spec_num_key"] = parsed_result.get('spec_num', "")

            # 2️⃣ [인스펙션 조회] (Inspectioncheck.py)
            if plate:
                res_status = Inspectioncheck.fetch_inspection_status(plate)
                st.session_state["inspection_status"] = res_status
                # 위젯용 변수에 저장
                st.session_state["v_inspection_key"] = res_status 

            # 3️⃣ [딜러 정보 조회] (dealerinfo.py)
            # 조회된 정보가 있으면 구글 시트 데이터를, 없으면 파싱된 주소를 사용
            dealer_found = False
            if contact:
                dealer_res = dealerinfo.search_dealer_info(contact)
                if dealer_res.get("status") == "success":
                    st.session_state["dealer_data"] = dealer_res
                    # 위젯 연결용 세션 변수들 업데이트
                    st.session_state["v_address_key"] = dealer_res.get("address", "")
                    st.session_state["v_biz_name_input"] = dealer_res.get("company", "")
                    st.session_state["v_biz_num_input"] = dealer_res.get("biz_num", "")
                    st.session_state["acc_o_input"] = dealer_res.get("acc_o", "")
                    st.session_state["acc_fee_input"] = dealer_res.get("acc_fee", "")
                    # 입금자명을 대문자로 변환하여 저장
                    sender_val = dealer_res.get("sender", "")
                    st.session_state["sender_input"] = sender_val.upper() if sender_val else ""
                    dealer_found = True
                else:
                    st.session_state["dealer_data"] = {}
            
            # 딜러 정보를 찾지 못한 경우 파싱된 주소 사용
            if not dealer_found:
                st.session_state["v_address_key"] = parsed_address
                # 지역 추출은 아래 5️⃣ 단계에서 통합 처리됨

            # 4️⃣ [바이어 국가 조회] (country.py)
            if buyer:
                country_res = country.handle_buyer_country(buyer, "")
                if country_res.get("status") == "fetched":
                    st.session_state["country_data"] = country_res["country"]

            # 5️⃣ [지역 추출] (mapping.py)
            # 세션에 저장된 주소를 기반으로 지역 매핑
            current_address = st.session_state.get("v_address_key", "")
            if current_address:
                detected_region = mapping.get_region_from_address(current_address)
                st.session_state["v_region_key"] = detected_region

            # 6️⃣ [차명 매핑 및 송금용 차명 결정] (google_sheet_manager.py)
            try:
                import google_sheet_manager as gsm
                car_map = gsm.get_car_name_map()
                alt_name = lg.get_alt_car_name(original_car_name, car_map)
                st.session_state["auto_alt_car_name"] = alt_name.upper() if alt_name else ""
            except:
                st.session_state["auto_alt_car_name"] = original_car_name.upper() if original_car_name else ""

            # 7️⃣ [기타 금액 데이터]
            st.session_state["parsed_data"] = parsed_result
            st.session_state["last_raw_input"] = raw_input
            st.session_state["last_raw_input"] = raw_input
            # 처리가 끝났으므로 페이지 재실행 (상단부터 다시 그리면서 값 채움)
            st.rerun()

# --- 매입사원 선택 및 차량 제원 정보 통합 행 ---
with st.container(border=True):
    # 컬럼 비율 조정 (중앙 제원 칸이 5개이므로 여유 있게 배분)
    row_top_cols = st.columns([1.5, 6, 1.5])

    with row_top_cols[0]:
        v_username = st.selectbox(
            "매입사원", 
            ["매입담당자", "임진수", "이민지", "이규성", "윤성준", "김태윤"], 
            index=0
        )

# --- 상단 제원 입력칸 섹션 ---
    with row_top_cols[1]:
        s1, s2, s3, s4, s5 = st.columns(5)
        
        # 버전 번호를 키에 포함 (예: "v_l_0", "v_l_1" ...)
        ver = st.session_state["widget_version"]
    
        # value는 세션 변수에서 가져오고, key는 버전을 포함시킴
        s1.text_input("길이", value=st.session_state.get("v_l", ""), key=f"v_l_{ver}")
        s2.text_input("너비", value=st.session_state.get("v_w", ""), key=f"v_w_{ver}")
        s3.text_input("높이", value=st.session_state.get("v_h", ""), key=f"v_h_{ver}")
        s5.text_input("중량", value=st.session_state.get("v_wt", ""), key=f"v_wt_{ver}")
        
        # CBM (기존 로직 유지)
        s4.text_input("CBM", value=st.session_state.get("v_c", "0.00"), key=f"v_c_{ver}")
    with row_top_cols[2]:
        v_spec_num = st.text_input("제원관리번호", key="v_spec_num_key")
    
# [핵심 수정] parsed 데이터를 세션에서 관리합니다.
if "parsed_data" not in st.session_state:
    st.session_state["parsed_data"] = {}



# 현재 화면에서 사용할 parsed 데이터 로드
parsed = st.session_state.get("parsed_data", {})
    
if "inspection_status" not in st.session_state:
    st.session_state["inspection_status"] = "X"
st.divider()
        
# --- 2. 메인 화면 구성 (70% : 30%) ---
col_info, col_list = st.columns([0.7, 0.3])

# --- [좌측: 매입정보 (70%)] ---
with col_info:
    d_data = st.session_state.get("dealer_data", {})
    title_col, insp_col = st.columns([3, 1])

    with title_col:
        st.markdown("### 🚗 매입 정보")

    with insp_col:
        insp_list = ["X", "S", "C"]
        # 세션 상태에서 현재 값을 가져오되, 없으면 기본값 "X"
        current_insp = st.session_state.get("inspection_status", "X")
        
        # index 추출 로직 (ValueError 방지)
        insp_idx = insp_list.index(current_insp) if current_insp in insp_list else 0
        
        st.selectbox(
            "Inspection", 
            options=insp_list, 
            index=insp_idx, 
            key="v_inspection_key", 
            label_visibility="collapsed"
        )

    st.divider()

   
    # R1: 차번호, 연식, 차명, 차명(송금용)
    r1_1, r1_2, r1_3, r1_4 = st.columns(4)
    v_plate = r1_1.text_input("차번호", value=parsed.get('plate', ""))
    v_year = r1_2.text_input("연식", value=parsed.get('year', ""))
    v_car_name = r1_3.text_input("차명", value=parsed.get('car_name', ""))
    default_alt_name = st.session_state.get("auto_alt_car_name", v_car_name)
    
    # 차명(송금용) - 실시간 대문자 변환을 위한 콜백 함수
    def uppercase_remit_name():
        val = st.session_state.get("remit_name_widget", "")
        st.session_state["remit_name_widget"] = val.upper()
    
    remit_input = r1_4.text_input(
        "차명(송금용)", 
        value=st.session_state.get("auto_alt_car_name", ""),
        key="remit_name_widget",
        on_change=uppercase_remit_name
    )
    v_car_name_remit = st.session_state.get("remit_name_widget", "")

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
    # dealer_data가 딕셔너리인지 한 번 더 확인하는 안전 장치
    d_data = st.session_state.get("dealer_data")
    if not isinstance(d_data, dict):
        d_data = {}
    
    # 주소 결정 (구글 시트 우선 -> 없으면 엑셀 파싱 데이터)
    sheet_address = d_data.get("address", "")
    parsed_address = parsed.get('address', "")
    final_address = sheet_address if sheet_address else parsed_address
    
    # R4: 연락처, 주소, 지역 (한 줄로 배치)
    r4_1, r4_2, r4_3 = st.columns([1.5, 3, 1.5])
    v_dealer_phone = r4_1.text_input("딜러연락처(phone)", value=parsed.get('dealer_phone', ""))
    v_address = r4_2.text_input(
        "주소(address)", 
        value=st.session_state.get("v_address_key", ""), 
        key="v_address_key",
        on_change=update_region
    )
    v_region = r4_3.text_input(
        "지역", 
        value=st.session_state.get("v_region_key", ""), 
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
    v_acc_o = acc2.text_input("차량대 계좌", value=d_data.get("acc_o", ""), key="acc_o_input")

    acc3, acc4 = st.columns([2, 3])
    v_contract_x = acc3.text_input("계산서X", value=pm.format_number(parsed.get('contract', "")))
    v_acc_x = acc4.text_input("계산서X 계좌", value=d_data.get("acc_x", ""))

    acc5, acc6 = st.columns([2, 3])
    v_fee = acc5.text_input("매도비", value=pm.format_number(parsed.get('fee', "")))
    v_acc_fee = acc6.text_input("매도비 계좌", value=d_data.get("acc_fee", ""))

    # 들여쓰기를 왼쪽으로 맞춰야 합니다.
    total_val = pm.calculate_total(v_price, v_contract_x, v_fee)
    
    # DECLARATION 자동 계산 및 세션 상태 저장
    auto_decl_val = pm.calculate_declaration(v_price)
    st.session_state["v_declaration_key"] = pm.format_number(auto_decl_val)
    
    r5_1, r5_2, r5_3, r5_4 = st.columns([2, 2, 2, 2])
    v_total = r5_1.text_input("합계금액 (자동계산)", value=pm.format_number(total_val), disabled=True)
    v_declaration = r5_2.text_input("DECLARATION", value=pm.format_number(auto_decl_val), key="v_declaration_key")
    sender_input = r5_3.text_input("입금자명", value=d_data.get("sender", ""), key="sender_input")
    v_sender = sender_input.upper() if sender_input else ""
    v_psource = r5_4.text_input(
    "P.Source", 
    key="v_psource" # 위젯 key를 세션 키와 일치시킴
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
                
    v_bizcl_num = v_biz_num.replace("-", "") if v_biz_num else ""

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

    # --- Tab 1: 문자전송 ---
    with tab1:
        input_data = {
            "year": v_year, "car_name": v_car_name, "plate": v_plate,
            "price": v_price, "fee": v_fee, "contract_x": v_contract_x,
            "sales": v_sales, "address": v_address, "dealer_phone": v_dealer_phone,
            "region": v_region, "site": v_site
        }
        
        # etc.py용 데이터 (입고방 알림, 서류안내 문자용)
        etc_data = {
            "plate": v_plate, "year": v_year, "car_name_remit": v_car_name_remit,
            "brand": v_brand, "vin": v_vin, "km": v_km, "color": v_color,
            "region": v_region, "sales": v_sales, "buyer": v_buyer, 
            "country": v_country, "inspection": st.session_state.get("v_inspection_key", "?"),
            "h_type": v_h_type, "h_id": v_h_id, "h_delivery": v_h_delivery,
            "price": v_price, "fee": v_fee, "contract_x": v_contract_x, 
            "deposit": v_deposit, "company": v_company, 
            "biz_name": v_biz_name, "biz_num": v_biz_num,
            "declaration": v_declaration, "ex_rate": v_ex_rate,
            "auc_type": v_auc_type, "auc_region": v_auc_region,
            "spec_num": v_spec_num
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

        if m_c1.button("아웃소싱(outsource)", key="btn_out"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "outsource")
            st.rerun()

        if m_c2.button("주소공유(address)", key="btn_share"):
            st.session_state["out_tab1_final"] = msg_logic.handle_confirm(input_data, "share_address")
            st.rerun()
        

        st.divider()
        
        current_content1 = st.session_state.get("out_tab1_final", "")
        
        # 2. 데이터가 있을 때만 출력창 보여주기
        if current_content1:
            st.markdown("##### 📄 생성된 메시지")
            st.caption("👇 우측 상단 복사 아이콘 클릭")
            # 언어 설정 language=None 혹은 language="markdown" 권장
            st.code(current_content1, language=None)
            
            # 리셋 버튼 배치
            if st.button("♻️ 내용 리셋", key="reset_tab1"):
                st.session_state["out_tab1_final"] = ""
                st.rerun()
        else:
            st.info("버튼을 클릭하면 메시지가 생성됩니다.")

    # --- Tab 2: 송금요청 ---
    with tab2:
        remit_data = {
            "plate": v_plate, "year": v_year, "car_name": v_car_name, "vin": v_vin,
            "address": v_address, "dealer_phone": v_dealer_phone,
            "price_acc": v_acc_o, "notbill_acc": v_acc_x, "fee_acc": v_acc_fee,
            "sender_name": v_sender, "brand": v_brand, "dealer_number": v_biz_num,
            "price": v_price, "fee": v_fee, "contract_x": v_contract_x,
            "total": v_total, "deposit": v_deposit, "balance": v_balance,
            "company": v_company, "ex_date": v_ex_date, "ex_rate": v_ex_rate,
            "usd_price": v_usd, "won_price": v_won, "car_name_remit": v_car_name_remit,
            "h_type": v_h_type, "h_id": v_h_id, "h_delivery": v_h_delivery,
            "spec_num": v_spec_num
        }
                # etc.py용 데이터 (입고방 알림, 서류안내 문자용)
        etc_data = {
            "plate": v_plate, "year": v_year, "car_name_remit": v_car_name_remit,
            "brand": v_brand, "vin": v_vin, "km": v_km, "color": v_color,
            "region": v_region, "sales": v_sales, "buyer": v_buyer, 
            "country": v_country, "inspection": st.session_state.get("v_inspection_key", "?"),
            "h_type": v_h_type, "h_id": v_h_id, "h_delivery": v_h_delivery,
            "price": v_price, "fee": v_fee, "contract_x": v_contract_x, 
            "deposit": v_deposit, "company": v_company, 
            "biz_name": v_biz_name, "biz_num": v_biz_num,
            "declaration": v_declaration, "ex_rate": v_ex_rate,
            "auc_type": v_auc_type, "auc_region": v_auc_region,
            "spec_num": v_spec_num
        }

        r_c1, r_c2 = st.columns(2)
        if r_c1.button("일반매입 송금", key="btn_remit_1"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "일반매입")
            st.rerun()
    
        if r_c2.button("계약금 송금", key="btn_remit_2"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "계약금")
            st.rerun()

        if r_c1.button("폐자원 송금", key="btn_remit_3"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "폐자원매입")
            st.rerun()

        if r_c2.button("송금완료 확인", key="btn_remit_4"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "송금완료")
            st.rerun()

        if r_c1.button("오토위니 송금", key="btn_remit_5"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "오토위니")
            st.rerun()

        if r_c2.button("헤이딜러 송금", key="btn_remit_6"):
            st.session_state["out_tab2_final"] = remit.handle_remit(remit_data, "헤이딜러")
            st.rerun()

                # Tab3에서 이동한 버튼들 (2열 구성 유지)
        if r_c1.button("입고방 알림", key="btn_etc1"):
            st.session_state["out_tab2_final"] = etc.handle_etc(etc_data, "입고방")
            st.rerun()
            
        if r_c2.button("서류안내 문자", key="btn_etc2"):
            st.session_state["out_tab2_final"] = etc.handle_etc(etc_data, "서류문자")
            st.rerun()

        if r_c1.button("🚀 정보등록", type="primary", key="btn_etc_reg"):
            with st.spinner("시트에 등록 중..."):
                res = inventoryenter.run_integrated_registration(etc_data)
                if res["status"] in ["success", "partial"]:
                    st.success(res["message"])
                else:
                    st.error(res["message"])

        st.divider()

        current_content2 = st.session_state.get("out_tab2_final", "")
        if current_content2:
            st.markdown("##### 💵 송금 요청서")
            st.caption("👇 우측 상단 복사 아이콘 클릭")
            st.code(current_content2, language=None)
            
            if st.button("♻️ 내용 리셋", key="reset_tab2"):
                st.session_state["out_tab2_final"] = ""
                st.rerun()
        else:
            st.info("송금 유형 버튼을 클릭하세요.")

    # --- Tab 3: 기타 ---
    # --- Tab 3: 기타 및 ERP 연동 ---
with tab3:

    # 1. 외부 링크 및 기본 정보 데이터 구성
    etc_data = {
        "plate": v_plate, "year": v_year, "car_name_remit": v_car_name_remit,
        "brand": v_brand, "vin": v_vin, "km": v_km, "color": v_color,
        "region": v_region, "sales": v_sales, "buyer": v_buyer, "dealer_phone": v_dealer_phone,
        "country": v_country, "inspection": st.session_state.get("v_inspection_key", "?"),
        "h_type": v_h_type, "h_id": v_h_id, "h_delivery": v_h_delivery,
        "price": v_price, "fee": v_fee, "contract_x": v_contract_x, 
        "deposit": v_deposit, "company": v_company, 
        "biz_name": v_biz_name, "biz_num": v_biz_num,
        "bizcl_num": v_bizcl_num,
        "declaration": v_declaration, "ex_rate": v_ex_rate, 
        "psource": st.session_state.get("v_psource", ""),
        "v_c": st.session_state.get("v_c", "0.00"),
        "length": st.session_state.get("v_l", "0"),
        "width": st.session_state.get("v_w", "0"),
        "height": st.session_state.get("v_h", "0"),
        "weight": st.session_state.get("v_wt", "0"),
        "spec_num": v_spec_num, "username" : v_username
    }

    st.markdown("### 🔍 차량 정보 및 제원 관리")
    e_c1, e_c2 = st.columns(2)
    
    with e_c1:
        # --- 좌측: 원본 사이트 이동 버튼 ---
        if v_site and v_site.startswith("http"):
            st.link_button("🌐 원본 사이트 이동", v_site, use_container_width=True)
        else:
            st.button("🌐 사이트 링크 없음", disabled=True, use_container_width=True)
            
# buyprogram.py 내의 e_c2 (제원조회 버튼) 부분 수정
    with e_c2:
            if st.button("📋 제원조회 실행", key="btn_run_spec_crawler", use_container_width=True, type="primary"):
                spec_val = st.session_state.get("v_spec_num_key", "")
                
                if spec_val:
                    with st.spinner("Cyberts 정보를 불러오는 중..."):
                        try:
                            res = cyberts_crawler.fetch_vehicle_specs(spec_val)
                            
                            if res.get("status") == "success":
                                data = res.get("data", {})
                                
                                # 1. 원본 데이터 세션 저장
                                l_str = data.get("length", "0")
                                w_str = data.get("width", "0")
                                h_str = data.get("height", "0")
                                
                                st.session_state["v_l"] = str(l_str)
                                st.session_state["v_w"] = str(w_str)
                                st.session_state["v_h"] = str(h_str)
                                st.session_state["v_wt"] = str(data.get("weight", ""))
                                
                                # 2. [추가] CBM 직접 계산 로직
                                try:
                                    # mm 단위를 m 단위로 변환하여 곱함 (L*W*H / 1,000,000,000)
                                    l_val = float(l_str)
                                    w_val = float(w_str)
                                    h_val = float(h_str)
                                    cbm_calc = (l_val * w_val * h_val) / 1000000000
                                    # 세션에 계산된 CBM 저장 (소수점 2자리)
                                    st.session_state["v_c"] = f"{cbm_calc:.2f}"
                                except:
                                    st.session_state["v_c"] = "0.00"
    
                                # 3. 위젯 버전 업데이트 및 리런
                                st.session_state["widget_version"] += 1
                                st.toast("✅ 제원 및 CBM 업데이트 완료!")
                                st.rerun()
                            else:
                                st.error(f"❌ 실패: {res.get('message')}")
                                
                        except Exception as e:
                            st.error(f"⚠️ 시스템 오류 발생: {e}")
                else:
                    st.warning("제원관리번호를 입력해주세요.")
    
    st.divider()

    # 2. 이카운트 ERP 구매입력 섹션
    st.divider()
    st.markdown("### 📊 이카운트 ERP 관리")
    if st.button("🚀 이카운트 데이터 동기화 및 구매입력", key="btn_integrated_ecount", type="primary", use_container_width=True):
        if not v_vin or not v_biz_num:
            st.error("⚠️ 차대번호와 사업자번호는 필수 입력 항목입니다.")
            st.stop()
        with st.spinner("구글 시트에서 NO. 정보를 조회 중..."):
        # 1. 구글 시트에서 NO. 값 가져오기
            found_no = gsm.get_no_by_plate(v_plate)
        
            if not found_no:
                st.warning("⚠️ 구글 시트 '2026'에서 해당 차량번호를 찾을 수 없어 제원관리번호로 대체합니다.")
                # 찾지 못했을 경우 기존처럼 v_spec_num을 사용하거나 빈값 처리
                final_spec_no = v_spec_num 
            else:
                final_spec_no = found_no
                st.info(f"✅ 구글 시트 NO. 확인: {final_spec_no}")
            etc_data["v_c"] = st.session_state.get("v_c", "0.00")
            
        with st.spinner("이카운트 작업 진행 중..."):
            # 0. 세션 획득
            session_id, login_error = ecount.get_session_id()
            if not session_id:
                st.error("❌ 이카운트 로그인 실패")
                st.json(login_error)
                st.stop()
    
            # 1. 품목 체크 및 등록
            item_exists, _ = ecount.check_item_exists(session_id, v_vin)
            if not item_exists:
                st.info(f"🔍 품목 미등록 확인: {v_vin} 등록 중...")
                res_item = ecount.register_item(etc_data, session_id, final_spec_no)
                err_msg = res_item.get("Data", {}).get("ResultDetails", [{}])[0].get("TotalError", "")
                # --- 디버깅용 로그 추가 ---
                st.write("📡 품목 등록 시도 응답:", res_item) 
                if "이미 품목등록에 존재하는 코드" in err_msg:
                    st.write("✔️ 확인 결과, 이미 등록된 품목입니다. (중복 등록 방지)")
                elif str(res_item.get("Status")) != "200" or res_item.get("Data", {}).get("SuccessCnt", 0) == 0:
                    st.error("❌ 품목 등록 실패")
                    st.json(res_item)
                    st.stop()
                else:
                    st.success("✅ 품목 등록 완료")
            else:
                st.write("✔️ 품목 확인 완료")
    
            # 2. 거래처 등록 시도 (조회 없이 바로 진행)
            st.info(f"🔄 거래처 확인 및 등록 시도: {v_biz_num}")
            res_cust = ecount.register_customer(etc_data, session_id)
            
            # 응답 데이터 안전하게 추출
            cust_data_part = res_cust.get("Data", {})
            cust_details = cust_data_part.get("ResultDetails", [])
            cust_err_msg = cust_details[0].get("TotalError", "") if cust_details else ""

            # 이카운트 응답에 따른 분기 처리
            if str(res_cust.get("Status")) == "200" and cust_data_part.get("SuccessCnt", 0) > 0:
                st.success("✅ 신규 거래처 등록 완료")
            elif "중복되는 코드는 등록할 수 없습니다" in cust_err_msg or "이미 등록된" in cust_err_msg:
                # 중복 에러가 나면 이미 있는 것이므로 성공으로 간주하고 진행
                st.write("✔️ 확인 결과, 이미 등록된 거래처입니다. (다음 단계 진행)")
            else:
                # 그 외의 진짜 에러(권한, 필수값 누락 등)인 경우에만 중단
                st.error("❌ 거래처 처리 중 오류 발생")
                st.json(res_cust)
                st.stop()
    
            # 3. 최종 구매입력 진행
            st.info("📝 구매전표 생성 중...")
            res_pur = ecount.register_purchase(etc_data, session_id, v_username)
            
            if str(res_pur.get("Status")) == "200":
                data_part = res_pur.get("Data", {})
                if data_part.get("SuccessCnt", 0) > 0:
                    st.balloons()
                    st.success(f"🎉 전표 생성 성공! 전표번호: {data_part.get('SlipNos')[0]}")
                else:
                    # 데이터 정합성 에러 (예: 창고코드 틀림 등)
                    st.error("❌ 전표 생성 실패 (데이터 에러)")
                    st.warning(data_part.get("ResultDetails", [{}])[0].get("TotalError", "상세 에러 확인 불가"))
                    with st.expander("전체 에러 로그 확인"):
                        st.json(res_pur)
            else:
                # 시스템/통신 에러
                st.error(f"❌ API 통신 실패: {res_pur.get('Message')}")
                st.json(res_pur)
    st.divider()
    st.markdown("### 🧪 API 권한 테스트")
    if st.button("🛠️ 거래처 등록 TEST 실행", key="btn_test_cust_reg", use_container_width=True):
        with st.spinner("샌드박스 서버로 테스트 데이터 전송 중..."):
            # 1. 세션 획득
            session_id, login_error = ecount.get_session_id()
            
            if session_id:
                # 2. 테스트 함수 호출
                test_res = ecount.register_customer_test(session_id)
                
                # 3. 결과 출력
                if str(test_res.get("Status")) == "200":
                    st.success("✅ 테스트 통신 성공!")
                    st.json(test_res) # 서버 응답 구조 확인용
                else:
                    st.error("❌ 테스트 실패")
                    st.json(test_res) # 에러 원인 분석용
            else:
                st.error("❌ 세션 획득 실패")
                st.json(login_error)
                
    st.divider()
    st.markdown("### 🤖 이카운트 웹 자동화 (Selenium)")
    
    if st.button("🚀 웹 방식 구매입력 실행", key="btn_web_automation", type="primary", use_container_width=True):
        if not v_vin or not v_price:
            st.warning("⚠️ 차대번호(VIN)와 차량대(Price) 정보가 입력되어야 합니다.")
        else:
            # 진행 상태창 생성
            with st.status("이카운트 자동 입력을 수행하고 있습니다...", expanded=True) as status_box:
                import ecountenter
                result = ecountenter.run_ecount_web_automation(etc_data, status_box)
                
                if result["status"] == "success":
                    status_box.update(label="🎉 구매입력 및 저장 성공!", state="complete", expanded=False)
                    st.balloons()
                else:
                    status_box.update(label="❌ 자동화 작업 실패", state="error")
                    st.error(f"실패 원인: {result['message']}")

    st.markdown("### ⚡ 데이터 통합 처리")
        
        # 통합입력 버튼 생성
    if st.button("🚀 통합입력 (시트 등록 + 알림)", key="btn_integrated_all", type="primary", use_container_width=True):
        with st.spinner("구글 시트 등록 및 데이터 처리를 진행 중입니다..."):
             # inventoryenter.py에 정의된 통합 등록 함수 호출
            res = inventoryenter.run_integrated_registration(etc_data)
                
             if res["status"] in ["success", "partial"]:
                   st.success(f"✅ 처리 완료: {res['message']}")
                   # 결과 내용을 화면 하단 출력칸에 저장하고 싶을 경우
                   st.session_state["out_tab3"] = res.get("message", "등록 성공")
                   st.balloons()
              else:
                   st.error(f"❌ 처리 실패: {res['message']}")

    # 3. 기타 알림 내용 출력칸 (기존 기능 유지)
    st.divider()
    current_content3 = st.session_state.get("out_tab3", "")
    if current_content3:
        st.markdown("##### ➕ 생성된 알림 내용")
        st.code(current_content3, language=None)
        if st.button("♻️ 내용 리셋", key="reset_tab3"):
            st.session_state["out_tab3"] = ""
            st.rerun()
    else:
        st.info("알림이나 전표 생성 버튼을 클릭하세요.")
