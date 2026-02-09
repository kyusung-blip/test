import streamlit as st

# 1. 10pt 폰트 및 스타일 설정
st.set_page_config(layout="wide") # 화면을 넓게 사용
st.markdown(
    """
    <style>
    html, body, [class*="css"], .stTextInput, .stNumberInput, .stSelectbox {
        font-size: 10pt !important;
    }
    .stButton button {
        font-size: 10pt !important;
        width: 100%; /* 버튼 너비를 꽉 차게 */
    }
    /* 입력창 간격 조절 */
    div.row-widget.stHorizontal {
        gap: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. 상단: 정보 붙여넣기 섹션 (탭 구분 데이터 입력)
st.subheader("📋 데이터 붙여넣기")
raw_data = st.text_area("텍스트 정보를 여기에 붙여넣으세요 (탭 구분)", height=100)

if raw_data:
    st.info("데이터를 분석 중입니다...") # 실제 분석 로직은 추후 추가 가능

st.divider()

# 3. 메인 상세 정보 섹션 (좌/우 컬럼 분할)
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.markdown("### 🚗 차량 기본 정보")
    st.text_input("차번호 (Vehicle Number)")
    st.text_input("연식 (Year)")
    st.text_input("차명 (Model)")
    st.text_input("차명(송금용) (Model for Remittance)")
    st.text_input("브랜드 (Brand)")
    st.text_input("VIN")
    
    c1, c2 = st.columns(2)
    c1.text_input("km")
    c2.text_input("color")
    
    st.text_input("주소 (Address)")
    
    c3, c4 = st.columns(2)
    c3.text_input("딜러연락처")
    c4.text_input("지역 (Region)")

    st.markdown("---")
    st.markdown("#### 🤝 딜러/판매자 정보 (Seller Info)")
    c5, c6 = st.columns(2)
    c5.text_input("상사명")
    c6.text_input("사업자번호")

with col_right:
    st.markdown("### 💰 정산 및 Autowini")
    st.text_input("차량대 (Vehicle Price)")
    st.text_input("계산서X (Invoice Not Issued)")
    st.text_input("매도비 (Sales Fee)")
    st.text_input("DECLARATION")
    st.text_input("합계금액 (Total Amount)")
    
    with st.expander("세부 정산(Calculation)", expanded=True):
        st.text_input("계약금(만원)")
        st.text_input("잔금 (Balance Payment)")

    with st.expander("★오토위니★Autowini", expanded=True):
        st.text_input("업체명 (Company Name)")
        st.text_input("환율기준일")
        st.text_input("환율")
        st.text_input("차량대금($)")

# 4. 하단 버튼 그룹 섹션
st.divider()
st.markdown("### 🛠️ 실행 제어")

# 버튼 레이아웃 (이미지 하단의 노란색/파란색 버튼들 재현)
row1 = st.columns(6)
row1[0].button("확인후")
row1[1].button("세일즈팀")
row1[2].button("검수자")
row1[3].button("문자")
row1[4].button("아웃소싱")
row1[5].button("주소공유")

row2 = st.columns(6)
row2[0].button("일반매입")
row2[1].button("폐차매입")
row2[2].button("계약금")
row2[3].button("송금완료")
row2[4].button("계약금 송금완료")
row2[5].button("오토위니/헤이딜러")
