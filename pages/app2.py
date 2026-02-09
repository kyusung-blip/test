import streamlit as st
import pandas as pd

# 1. 페이지 설정 및 10pt 폰트 스타일 정의
st.set_page_config(layout="wide", page_title="차량 매매 관리 시스템")

st.markdown(
    """
    <style>
    /* 전체 폰트 크기 10pt 설정 */
    html, body, [class*="css"], .stTextInput, .stNumberInput, .stSelectbox, .stTextArea, .stButton {
        font-size: 10pt !important;
    }
    
    /* 버튼 스타일 조정 */
    .stButton button {
        height: 3em;
        border-radius: 5px;
    }
    
    /* 하단 출력창 스타일 */
    .output-container {
        background-color: #f8f9fa;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 10px;
        min-height: 200px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. 상단: 정보 붙여넣기 및 데이터 파싱 로직
st.subheader("📋 데이터 붙여넣기 (Tab 구분)")
raw_input = st.text_area("텍스트를 여기에 붙여넣으세요.", height=70, placeholder="데이터를 붙여넣으면 아래 칸들이 자동으로 채워집니다 (구현 예정)")

# (참고) 나중에 raw_input.split('\t')를 이용해 아래 value값들에 할당할 수 있습니다.
parsed_data = {} 

st.divider()

# 3. 메인 상세 정보 섹션 (좌/우 컬럼 분할)
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("### 🚗 차량 기본 정보")
    v_num = st.text_input("차번호 (Vehicle Number)")
    v_year = st.text_input("연식 (Year)")
    v_model = st.text_input("차명 (Model)")
    v_remit = st.text_input("차명(송금용) (Model for Remittance)")
    v_brand = st.text_input("브랜드 (Brand)")
    v_vin = st.text_input("VIN")
    
    c1, c2 = st.columns(2)
    with c1: v_km = st.text_input("km")
    with c2: v_color = st.text_input("color")
    
    st.text_input("주소 (Address)")
    
    c3, c4 = st.columns(2)
    with c3: st.text_input("딜러연락처")
    with c4: st.text_input("지역 (Region)")

    st.markdown("#### 🤝 딜러/판매자 정보")
    c5, c6 = st.columns(2)
    with c5: st.text_input("상사명")
    with c6: st.text_input("사업자번호")

with col_right:
    st.markdown("### 💰 정산 및 Autowini")
    st.text_input("차량대 (Vehicle Price)")
    st.text_input("계산서X (Invoice Not Issued)")
    st.text_input("매도비 (Sales Fee)")
    st.text_input("합계금액 (Total Amount)")
    
    with st.expander("📝 세부 정산(Calculation)", expanded=True):
        st.text_input("계약금(만원)")
        st.text_input("잔금 (Balance Payment)")

    with st.expander("⭐ 오토위니 (Autowini)", expanded=True):
        st.text_input("업체명 (Company Name)")
        st.text_input("환율")
        st.text_input("차량대금($)")
        st.text_input("영세율금액(원)")

st.divider()

# 4. 하단: 실행 제어 버튼 그룹
st.markdown("### 🛠️ 실행 제어")
r1_c1, r1_c2, r1_c3, r1_c4, r1_c5, r1_c6 = st.columns(6)
btn_confirm = r1_c1.button("✅ 확인후")
btn_sales = r1_c2.button("👥 세일즈팀")
btn_inspect = r1_c3.button("🔍 검수자")
btn_sms = r1_c4.button("💬 문자전송")
btn_out = r1_c5.button("📦 아웃소싱")
btn_reset = r1_c6.button("🔄 내용리셋", type="secondary")

# 5. 최종 결과 출력 섹션
st.markdown("### 📝 결과 출력")
output_box = st.container()

with output_box:
    # 버튼 클릭에 따른 로직 처리
    if btn_confirm:
        st.success("데이터가 확인되었습니다.")
        st.code(f"차량번호: {v_num}\n모델: {v_model}\n상태: 확인 완료", language=None)
        
    elif btn_sms:
        st.info("문자 발송 양식 생성")
        sms_text = f"[광고] {v_num} 차량 매입 절차 안내..."
        st.text_area("결과 복사", value=sms_text, height=100)
        
    elif btn_reset:
        st.warning("내용이 초기화되었습니다. (화면을 새로고침 하세요)")
        
    else:
        st.info("상단 버튼을 클릭하면 이곳에 결과가 출력됩니다.")
