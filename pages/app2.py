import streamlit as st

# 1. 스타일 설정 (10pt 폰트 유지)
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton {
        font-size: 10pt !important;
    }
    /* 출력창 배경색 및 테두리 설정 */
    .output-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #d1d5db;
        font-family: monospace;
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

st.subheader("📋 데이터 붙여넣기")
raw_data = st.text_area("텍스트 정보를 여기에 붙여넣으세요", height=80)
st.divider()

# 메인 레이아웃 (좌/우)
col_left, col_right = st.columns([1.5, 1])
with col_left:
    vehicle_num = st.text_input("차번호", value="12가3456") # 예시 데이터
    model = st.text_input("차명", value="아반떼 CN7")
with col_right:
    price = st.text_input("합계금액", value="15,000,000")

st.divider()

# 2. 하단 실행 제어 버튼부
st.markdown("### 🛠️ 실행 제어")
row1 = st.columns(6)
btn_confirm = row1[0].button("확인후")
btn_sales = row1[1].button("세일즈팀")
btn_sms = row1[3].button("문자")

# 3. ✨ 결과 출력 섹션 (Output Section)
st.markdown("---")
st.markdown("### 📝 결과 출력")

# 버튼 클릭 상태에 따라 다른 내용을 출력하도록 설정
output_container = st.container()

with output_container:
    if btn_confirm:
        st.success("✅ 확인후 프로세스가 실행되었습니다.")
        result_text = f"[{vehicle_num} / {model}] 확인 완료되었습니다."
        st.code(result_text, language=None) # 복사하기 쉬운 코드 블록 형태
        
    elif btn_sales:
        st.info("📨 세일즈팀 전달용 정보")
        result_text = f"차량번호: {vehicle_num}\n모델명: {model}\n금액: {price}\n담당자: 세일즈 1팀"
        st.text_area("복사용 텍스트", value=result_text, height=150)

    elif btn_sms:
        st.warning("📱 문자 발송 양식")
        result_text = f"[광고] 안녕하세요. 요청하신 {vehicle_num} 차량 견적은 {price}원 입니다."
        st.markdown(f'<div class="output-box">{result_text}</div>', unsafe_allow_html=True)
        
    else:
        st.write("버튼을 누르면 이곳에 결과가 표시됩니다.")
