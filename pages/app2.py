import streamlit as st

# 1. 페이지 설정: 화면을 넓게 쓰고 제목 설정
st.set_page_config(layout="wide", page_title="차량 매매 통합 관리 시스템")

# 2. CSS를 이용한 스타일 제어 (10pt 폰트 및 레이아웃)
st.markdown(
    """
    <style>
    /* 전체 폰트 크기 10pt */
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton, .stSelectbox {
        font-size: 10pt !important;
    }
    
    /* 오른쪽 출력창 배경 및 테두리 스타일 */
    .output-box {
        background-color: #f8f9fa;
        padding: 15px;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        min-height: 600px;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* 버튼 사이 간격 조절 */
    .stButton button {
        width: 100%;
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 3. 메인 레이아웃 분할 (왼쪽 70% : 오른쪽 30%)
col_left, col_right = st.columns([0.7, 0.3])

# --- [좌측 섹션: 입력 및 제어] ---
with col_left:
    st.subheader("📋 데이터 붙여넣기 및 상세 정보")
    
    # 상단 텍스트 입력 엔트리 (데이터 파싱용)
    raw_data = st.text_area("텍스트 정보를 여기에 붙여넣으세요 (Tab 구분 데이터)", height=100)
    
    st.divider()
    
    # 상세 정보 레이아웃 (좌/우 분할)
    detail_col1, detail_col2 = st.columns([1.2, 1])
    
    with detail_col1:
        st.markdown("**🚗 차량 기본 정보**")
        v_num = st.text_input("차번호 (Vehicle Number)")
        v_year = st.text_input("연식 (Year)")
        v_model = st.text_input("차명 (Model)")
        v_brand = st.text_input("브랜드 (Brand)")
        
        c_sub1, c_sub2 = st.columns(2)
        v_km = c_sub1.text_input("km")
        v_color = c_sub2.text_input("color")
        
        st.text_input("주소 (Address)")

    with detail_col2:
        st.markdown("**💰 정산 및 결제 정보**")
        v_price = st.text_input("차량대 (Vehicle Price)")
        v_total = st.text_input("합계금액 (Total Amount)")
        
        with st.expander("세부 정산(Calculation)", expanded=True):
            st.text_input("계약금(만원)")
            st.text_input("잔금 (Balance Payment)")
            
        with st.expander("★오토위니/헤이딜러", expanded=True):
            st.text_input("업체명")
            st.text_input("환율")

    st.divider()

    # 하단 버튼 그룹 (실행 제어)
    st.markdown("**🛠️ 실행 제어**")
    
    # 버튼을 여러 줄로 배치 (이미지 참고)
    btn_row1 = st.columns(5)
    btn_confirm = btn_row1[0].button("확인후")
    btn_sales = btn_row1[1].button("세일즈팀")
    btn_inspect = btn_row1[2].button("검수자")
    btn_sms = btn_row1[3].button("문자")
    btn_outsourcing = btn_row1[4].button("아웃소싱")
    
    btn_row2 = st.columns(5)
    btn_regular = btn_row2[0].button("일반매입")
    btn_scrap = btn_row2[1].button("폐차매입")
    btn_done = btn_row2[2].button("송금완료")
    btn_reset = btn_row2[4].button("내용리셋", type="secondary")

# --- [우측 섹션: 결과 출력] ---
with col_right:
    st.subheader("📝 결과 출력")
    
    # 버튼 클릭에 따른 결과 처리 로직
    if btn_confirm:
        with st.container():
            st.markdown('<div class="output-box">', unsafe_allow_html=True)
            st.success("✅ 정보 확인 완료")
            st.write(f"**차량번호:** {v_num}")
            st.write(f"**모델:** {v_model}")
            st.write(f"**합계금액:** {v_total}")
            st.markdown('</div>', unsafe_allow_html=True)
            
    elif btn_sms:
        with st.container():
            st.markdown('<div class="output-box">', unsafe_allow_html=True)
            st.info("📱 문자 발송 양식")
            sms_text = f"[매입안내]\n차량: {v_num}\n금액: {v_total}\n담당자에게 문의 바랍니다."
            st.text_area("복사용 텍스트", value=sms_text, height=200)
            st.markdown('</div>', unsafe_allow_html=True)
            
    elif btn_sales:
        with st.container():
            st.markdown('<div class="output-box">', unsafe_allow_html=True)
            st.code(f"세일즈팀 전달 사항\n----------------\n차량: {v_model}\n금액: {v_price}", language=None)
            st.markdown('</div>', unsafe_allow_html=True)
            
    else:
        # 기본 대기 상태
        st.markdown(
            '<div class="output-box" style="color: gray;">'
            '왼쪽의 버튼을 클릭하면<br>이곳에 결과가 표시됩니다.'
            '</div>', 
            unsafe_allow_html=True
        )
