import streamlit as st
import re
from datetime import datetime
import logic as lg  # 작성한 logic.py 임포트
import price_manager as pm # price_manager를 pm이라는 별칭으로 가져옵니다.
import message as msg_logic

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
raw_input = st.text_area("엑셀 데이터를 이곳에 붙여넣으세요", height=100, placeholder="엑셀 행 전체를 복사해서 붙여넣으면 하단에 자동 입력됩니다.")

# 데이터가 입력되면 즉시 파싱 수행
parsed = lg.parse_excel_data(raw_input) if raw_input else {}

st.divider()

# --- 2. 메인 화면 구성 (70% : 30%) ---
col_info, col_list = st.columns([0.7, 0.3])

# --- [좌측: 매입정보 (70%)] ---
with col_info:
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
    v_country = r3_4.text_input("나라", value="")
    r3_5.write("") 
    if r3_5.button("확인"):
        st.toast("정보가 확인되었습니다.")

    # R4: 연락처, 지역, 주소
    r4_1, r4_2, r4_3 = st.columns([1.5, 1.5, 3])
    v_dealer_phone = r4_1.text_input("딜러연락처", value=parsed.get('dealer_phone', ""))
    v_region = r4_2.text_input("지역", value=parsed.get('region', ""))
    v_address = r4_3.text_input("주소", value=parsed.get('address', ""))

    # 딜러/판매자 정보 프레임
    with st.container(border=True):
        st.caption("🏢 딜러/판매자 정보")
        c1, c2 = st.columns(2)
        v_biz_name = c1.text_input("상사명", value="") 
        v_biz_num = c2.text_input("사업자번호", value="")

    # 계좌 정보 섹션
    acc1, acc2 = st.columns([2, 3])
    # 엑셀에서 가져온 원본 숫자를 "1,300만원" 형식으로 변환하여 표시
    v_price = acc1.text_input("차량대", value=pm.format_number(parsed.get('price', "")))
    v_acc_o = acc2.text_input("차량대 계좌", value="")

    acc3, acc4 = st.columns([2, 3])
    v_contract_x = acc3.text_input("계산서X", value=pm.format_number(parsed.get('contract', "")))
    v_acc_x = acc4.text_input("계산서X 계좌", value="")

    acc5, acc6 = st.columns([2, 3])
    v_fee = acc5.text_input("매도비", value=pm.format_number(parsed.get('fee', "")))
    v_acc_fee = acc6.text_input("매도비 계좌", value="")

    # 💡 [핵심] 실시간 합계 계산
    # 입력창에 써있는 글자들을 숫자로 바꿔서 더함
    total_val = pm.calculate_total(v_price, v_contract_x, v_fee)
    # 3. 합계금액 입력창을 만듭니다. (이때 v_total 변수가 생성됨)
    v_total = st.text_input("합계금액", value=pm.format_number(total_val))

    r5_1, r5_2, r5_3 = st.columns([1.5, 1, 1])
    v_sender = r5_1.text_input("입금자명", value="서북인터")
    if r5_2.button("🏦 계좌확인"):
        pass
    if r5_3.button("📝 정보 추가&수정", type="primary"):
        pass

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
            v_h_deliv = st.text_input("헤이딜러 탁송", value=parsed.get('heydlr_delivery', ""))

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
        
        b1, b2 = st.columns(2)
        with b1:
            if st.button("📋 내용복사", key="cp1"):
                content = st.session_state.get("out_tab1_final", "")
                if content:
                    st.copy_to_clipboard(content)
                    st.toast("클립보드에 복사되었습니다!", icon="✅")
                else:
                    st.toast("복사할 내용이 없습니다.", icon="⚠️")
        with b2:
            if st.button("♻️ 내용리셋", key="rs1"):
                st.session_state["out_tab1_final"] = ""
                st.rerun()

        # 내용 리셋 버튼 (세션 상태 직접 수정)
        if b2.button("♻️ 내용리셋", key="rs1"):
            st.session_state["out_tab1_final"] = ""  # 위젯의 key값을 초기화
            st.rerun()

    with tab2:
    # 데이터 수집 (입력창 변수들)
    remit_data = {
        "plate": v_plate, "year": v_year, "car_name": v_car_name, "vin": v_vin,
        "address": v_address, "dealer_phone": v_dealer_phone,
        "price_acc": v_acc_o, "notbill_acc": v_acc_x, "fee_acc": v_acc_fee,
        "sender_name": v_sender, "brand": v_brand, "dealer_number": v_dealer_num,
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
        b3, b4 = st.columns(2)
        if b3.button("📋 내용복사", key="cp2"):
            content_to_copy = st.session_state.get("out_tab1_final", "")
            if content_to_copy:
                st.copy_to_clipboard(content_to_copy) # 클립보드로 직접 전송
                st.toast("클립보드에 복사되었습니다! (Ctrl+V 가능)", icon="✅")
            else:
                st.warning("복사할 내용이 없습니다.")

        # 내용 리셋 버튼 (세션 상태 직접 수정)
        if b4.button("♻️ 내용리셋", key="rs2"):
            st.session_state["out_tab1_final"] = ""  # 위젯의 key값을 초기화
            st.rerun()

    with tab3:
        e_c1, e_c2 = st.columns(2)
        if e_c1.button("입고방"): pass
        if e_c2.button("정보등록"): pass
        if e_c1.button("서류문자"): pass
        if e_c2.button("사이트"): pass
        
        st.text_area("기타 메시지 결과", height=400, key="out_tab3")
        b5, b6 = st.columns(2)
        if b5.button("📋 내용복사", key="cp3"):
            content_to_copy = st.session_state.get("out_tab1_final", "")
            if content_to_copy:
                st.copy_to_clipboard(content_to_copy) # 클립보드로 직접 전송
                st.toast("클립보드에 복사되었습니다! (Ctrl+V 가능)", icon="✅")
            else:
                st.warning("복사할 내용이 없습니다.")

        # 내용 리셋 버튼 (세션 상태 직접 수정)
        if b6.button("♻️ 내용리셋", key="rs3"):
            st.session_state["out_tab1_final"] = ""  # 위젯의 key값을 초기화
            st.rerun()
