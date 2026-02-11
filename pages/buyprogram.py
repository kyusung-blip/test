import streamlit as st
import re
from datetime import datetime
import logic as lg  # 작성한 logic.py 임포트
import price_manager as pm # price_manager를 pm이라는 별칭으로 가져옵니다.
import message as msg_logic
import remit
import etc
import dealerinfo
import country
import mapping

# --- 페이지 방문 체크 및 자동 리셋 (최상단) ---
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "buyprogram"

# 다른 페이지에서 넘어온 경우 세션 초기화
if st.session_state["current_page"] != "buyprogram":
    keys_to_delete = ["dealer_data", "last_searched_phone", "detected_region", "country_data", "last_searched_buyer", "raw_input_main"]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["current_page"] = "buyprogram"

# parsed 변수는 항상 루프 시작 시 빈 딕셔너리로 초기화
parsed = {}

# --- 0. 기본 설정 ---
st.set_page_config(layout="wide", page_title="서북인터내셔널 매매 시스템")

# CSS 스타일 유지
st.markdown("""
    <style>
    .stButton>button { width: 100%; margin-bottom: 5px; }
    .stExpander { border: 1px solid #f0f2f6; border-radius: 5px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'output_text' not in st.session_state:
    st.session_state.output_text = ""

# --- 1. 상단: 데이터 입력칸 및 자동 파싱 ---
st.subheader("📥 데이터 붙여넣기")

# 리셋 버튼을 위해 컬럼 나눔
top_col1, top_col2 = st.columns([8, 1])

with top_col2:
    if st.button("♻️ 전체 리셋"):
        # 삭제할 세션 키 리스트
        keys_to_clear = [
            "dealer_data", "last_searched_phone", "detected_region", 
            "country_data", "last_searched_buyer", "raw_input_main"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key] # 빈 문자열이 아니라 아예 삭제!
        
        # 텍스트 에어리어 등 위젯 상태 강제 초기화
        st.rerun()
        
raw_input = st.text_area("엑셀 데이터를 이곳에 붙여넣으세요", height=100, placeholder="엑셀 행 전체를 복사해서 붙여넣으면 하단에 자동 입력됩니다.")

parsed = {}

# 데이터가 입력되었을 때만 실행
if raw_input:
    # 1. 엑셀 파싱
    parsed = lg.parse_excel_data(raw_input)
    
    # 2. 파싱된 연락처가 있고, 아직 조회를 안 했거나 연락처가 바뀌었을 때 자동 조회
    contact = parsed.get('dealer_phone', "")
    if contact and st.session_state.get('last_searched_phone') != contact:
        with st.spinner("딜러 정보를 불러오는 중..."):
            dealer_res = dealerinfo.search_dealer_info(contact)
            if dealer_res["status"] == "success":
                st.session_state["dealer_data"] = dealer_res
                st.session_state["last_searched_phone"] = contact
                st.toast(f"✅ {dealer_res['company']} 정보 로드 완료")
            else:
                # 정보를 못 찾아도 빈 데이터로 초기화 (이전 데이터 남지 않게)
                st.session_state["dealer_data"] = {}
                st.session_state["last_searched_phone"] = contact
                
    final_address = st.session_state.get("dealer_data", {}).get("address")
    if not final_address:
        final_address = parsed.get("address", "")
    
    # 판별된 지역을 세션에 저장
    detected_region = mapping.get_region_from_address(final_address)
    if detected_region:
        st.session_state["detected_region"] = detected_region
                
    buyer = parsed.get('buyer', "").strip()
    if buyer and st.session_state.get('last_searched_buyer') != buyer:
        res = country.handle_buyer_country(buyer, "") # 나라 정보 조회
        if res["status"] == "fetched":
            st.session_state["country_data"] = res["country"]
            st.session_state["last_searched_buyer"] = buyer
            st.toast(f"🌍 {buyer}의 나라 정보를 불러왔습니다.")

st.divider()

# --- 2. 메인 화면 구성 (70% : 30%) ---
col_info, col_list = st.columns([0.7, 0.3])

# --- [좌측: 매입정보 (70%)] ---
with col_info:
    d_data = st.session_state.get("dealer_data", {})
    st.markdown("### 🚗 매입 정보")
    
    # R1: 차번호, 연식, 차명, 차명(송금용)
    r1_1, r1_2, r1_3, r1_4 = st.columns(4)
    v_plate = r1_1.text_input("차번호", value=parsed.get('plate', ""))
    v_year = r1_2.text_input("연식", value=parsed.get('year', ""))
    v_car_name = r1_3.text_input("차명", value=parsed.get('car_name', ""))
    v_car_name_remit = r1_4.text_input("차명(송금용)", value=parsed.get('car_name', ""))

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
    v_region = r4_2.text_input(
    "지역", 
    value=st.session_state.get("detected_region", parsed.get('region', "")), 
    key="v_region_key"
    )
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

    # 딜러/판매자 정보 프레임
    with st.container(border=True):
        st.caption("🏢 딜러/판매자 정보")
        c1, c2 = st.columns(2)
        v_biz_name = c1.text_input("상사명", value=d_data.get("company", ""), key="v_biz_name_input")
        v_biz_num = st.text_input(
        "사업자번호", 
        value=d_data.get("biz_num") if d_data.get("biz_num") else parsed.get('dealer_number', ""),
        key="biz_num_input"
        )

    # 계좌 정보 섹션
    acc1, acc2 = st.columns([2, 3])
    # 엑셀에서 가져온 원본 숫자를 "1,300만원" 형식으로 변환하여 표시
    v_price = acc1.text_input("차량대", value=pm.format_number(parsed.get('price', "")))
    v_acc_o = st.text_input(
    "차량대 계좌", 
    value=d_data.get("acc_o", ""),
    key="acc_o_input"
    )

    acc3, acc4 = st.columns([2, 3])
    v_contract_x = acc3.text_input("계산서X", value=pm.format_number(parsed.get('contract', "")))
    v_acc_x = acc4.text_input("계산서X 계좌", value=d_data.get("acc_x", ""))

    acc5, acc6 = st.columns([2, 3])
    v_fee = acc5.text_input("매도비", value=pm.format_number(parsed.get('fee', "")))
    v_acc_fee = acc6.text_input("매도비 계좌", value=d_data.get("acc_fee", ""))

    # 💡 [핵심] 실시간 합계 계산
    # 입력창에 써있는 글자들을 숫자로 바꿔서 더함
    total_val = pm.calculate_total(v_price, v_contract_x, v_fee)
    # 3. 합계금액 입력창을 만듭니다. (이때 v_total 변수가 생성됨)
    v_total = st.text_input("합계금액", value=pm.format_number(total_val))

    r5_1, r5_2, r5_3 = st.columns([1.5, 1, 1])
    v_sender = st.text_input(
    "입금자명", 
    value=d_data.get("sender", "서북인터"),
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
    
        st.text_area("송금 요청 결과", height=300, key="out_tab2_final")
        content2 = st.session_state.get("out_tab2", "")
        if content2:
            st.caption("👇 우측 상단 복사 아이콘 클릭")
            st.code(content2, language=None)

        if st.button("♻️ 내용리셋", key="rs2"):
            st.session_state["out_tab2"] = ""
            st.rerun()

    with tab3:
        etc_data = {
            "buyer": v_buyer, "region": v_region, "vin": v_vin, "km": v_km,
            "plate": v_plate, "year": v_year, "car_name_remit": v_car_name_remit,
            "h_type": v_h_type, "h_id": v_h_id,
            "auc_type": v_auc_type, "auc_region": v_auc_region
        }
        e_c1, e_c2 = st.columns(2)
        if e_c1.button("입고방 알림", key="btn_etc1"):
            st.session_state["out_tab3"] = etc.handle_etc(etc_data, "입고방")
            st.rerun()
        if e_c2.button("정보등록"): pass
        if e_c2.button("서류안내 문자", key="btn_etc2"):
            st.session_state["out_tab3"] = etc.handle_etc(etc_data, "서류문자")
            st.rerun()
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
