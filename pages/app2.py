import streamlit as st

# 1. 페이지 설정 및 10pt 스타일 유지
st.set_page_config(layout="wide", page_title="차량 매매 통합 관리 시스템")

st.markdown(
    """
    <style>
    /* 전체 폰트 크기 10pt */
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton, .stSelectbox {
        font-size: 10pt !important;
    }
    
    /* 오른쪽 출력창 스타일 */
    .output-box {
        background-color: #f8f9fa;
        padding: 15px;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        min-height: 800px;
        font-family: 'Courier New', Courier, monospace;
    }

    /* 버튼 높이 및 스타일 */
    .stButton button {
        width: 100%;
        height: 2.5em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 2. 메인 레이아웃 분할 (좌측 70% : 우측 30%)
col_left, col_right = st.columns([0.7, 0.3])

# --- [좌측 섹션: 입력 및 제어] ---
with col_left:
    st.subheader("📋 상세 정보 입력")
    
    # 상단 데이터 붙여넣기
    raw_data = st.text_area("데이터 붙여넣기 (Tab 구분)", height=80)
    st.divider()

    # 입력란 구성
    L_col, R_col = st.columns([1.2, 1])

    with L_col:
        st.markdown("**🚗 차량 기본 정보**")
        st.text_input("차번호")
        st.text_input("연식")
        st.text_input("차명")
        st.text_input("차명(송금용)") # 요청 추가
        
        c1, c2 = st.columns(2)
        c1.text_input("km")
        c2.text_input("color")
        
        st.text_input("주소")
        
        # 딜러연락처 / 지역 (요청 추가)
        c3, c4 = st.columns(2)
        c3.text_input("딜러연락처")
        c4.text_input("지역")

        # 딜러/판매자 정보 프레임 (요청 추가)
        with st.expander("🤝 딜러/판매자 정보", expanded=True):
            c5, c6 = st.columns(2)
            c5.text_input("상사명")
            c6.text_input("사업자번호")
        
        # 계좌 정보 섹션 (요청 추가)
        st.text_input("차량대계좌")
        st.text_input("매도비계좌")
        
        # 입금자명 및 관련 버튼 (요청 추가)
        c7, c8, c9 = st.columns([2, 1, 1])
        c7.text_input("입금자명")
        c8.write("") # 간격 맞추기용
        c8.button("계좌확인")
        c9.write("")
        c9.button("정보추가&수정")

        # 바이어/나라 및 확인 버튼 (요청 추가)
        c10, c11, c12 = st.columns([2, 1, 1])
        c10.text_input("바이어명")
        c11.text_input("나라")
        c12.write("")
        btn_confirm_info = c12.button("확인")

    with R_col:
        st.markdown("**💰 정산 및 결제 정보**")
        st.text_input("차량대")
        st.text_input("계산서X")
        st.text_input("매도비")
        st.text_input("합계금액")
        
        with st.expander("📝 세부 정산(Calculation)", expanded=True):
            st.text_input("계약금(만원)")
            st.text_input("잔금")
            
        with st.expander("⭐ 오토위니/헤이딜러", expanded=True):
            st.text_input("업체명")
            st.text_input("환율")
            st.text_input("차량대금($)")

    st.divider()

    # 실행 제어 버튼 그룹
    st.markdown("**🛠️ 실행 제어**")
    row1 = st.columns(6)
    btn_confirm = row1[0].button("확인후")
    btn_sales = row1[1].button("세일즈팀")
    btn_inspect = row1[2].button("검수자")
    btn_sms = row1[3].button("문자")
    btn_out = row1[4].button("아웃소싱")
    btn_addr = row1[5].button("주소공유")

    row2 = st.columns(6)
    btn_reg = row2[0].button("일반매입")
    btn_scrap = row2[1].button("폐차매입")
    btn_down = row2[2].button("계약금")
    btn_remit = row2[3].button("송금완료")
    btn_reset = row2[5].button("내용리셋", type="secondary")

# --- [우측 섹션: 결과 출력] ---
with col_right:
    st.subheader("📝 결과 출력")
    
    output_area = st.container()
    with output_area:
        st.markdown('<div class="output-box">', unsafe_allow_html=True)
        if btn_confirm:
            st.success("데이터 확인 완료")
            st.write("확인후 프로세스가 시작되었습니다.")
        elif btn_sms:
            st.info("문자 양식 생성")
            st.text_area("SMS 복사", value="[안내] 차량 매입 건...", height=200)
        elif btn_reset:
            st.warning("리셋되었습니다.")
        else:
            st.write("버튼을 누르면 결과가 표시됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)
