import streamlit as st

# 1. 페이지 설정 및 10pt 스타일 설정
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
        min-height: 850px;
        font-family: 'Courier New', Courier, monospace;
    }

    /* 버튼 스타일 */
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
    raw_data = st.text_area("데이터 붙여넣기 (Tab 구분)", height=70)
    st.divider()

    L_col, R_col = st.columns([1.1, 1])

    with L_col:
        st.markdown("**🚗 차량 기본 정보**")
        st.text_input("차번호")
        st.text_input("연식")
        st.text_input("차명")
        st.text_input("차명(송금용)")
        
        c1, c2 = st.columns(2)
        c1.text_input("km")
        c2.text_input("color")
        st.text_input("주소")
        
        c3, c4 = st.columns(2)
        c3.text_input("딜러연락처")
        c4.text_input("지역")

        with st.expander("🤝 딜러/판매자 정보", expanded=True):
            c5, c6 = st.columns(2)
            c5.text_input("상사명")
            c6.text_input("사업자번호")
        
        st.text_input("차량대계좌")
        st.text_input("매도비계좌")
        
        c7, c8, c9 = st.columns([2, 1, 1])
        c7.text_input("입금자명")
        c8.markdown("<br>", unsafe_allow_html=True) # 줄맞춤
        c8.button("계좌확인")
        c9.markdown("<br>", unsafe_allow_html=True)
        c9.button("정보추가&수정")

        c10, c11, c12 = st.columns([2, 1, 1])
        c10.text_input("바이어명")
        c11.text_input("나라")
        c12.markdown("<br>", unsafe_allow_html=True)
        c12.button("확인", key="buyer_confirm")

    with R_col:
        st.markdown("**💰 정산 및 결제 정보**")
        st.text_input("차량대")
        st.text_input("계산서X")
        st.text_input("매도비")
        st.text_input("DECLARATION") # 추가
        st.text_input("합계금액")
        
        with st.expander("📝 세부 정산(Calculation)", expanded=True):
            st.text_input("계약금(만원)")
            st.text_input("잔금")
            
        with st.expander("⭐ 오토위니", expanded=True): # 명칭 변경
            st.text_input("업체명")
            st.text_input("환율기준일") # 추가
            
            c_ex1, c_ex2 = st.columns([3, 1])
            c_ex1.text_input("환율")
            c_ex2.markdown("<br>", unsafe_allow_html=True)
            c_ex2.button("환율") # 환율 버튼 추가
            
            st.text_input("차량대금($)")
            st.text_input("영세율금액(원)") # 추가

        # 오토위니 프레임 아래 추가 정보
        st.markdown("**🏷️ 기타 플랫폼 정보**")
        c_p1, c_p2 = st.columns(2)
        c_p1.text_input("사이트")
        c_p2.text_input("세일즈팀")

        c_h1, c_h2 = st.columns(2)
        c_h1.selectbox("헤이딜러 종류", ["선택 안함", "제로", "셀프"], index=0)
        c_h2.selectbox("헤이딜러 ID", ["선택 안함", "ID_1", "ID_2"], index=0)
        
        st.text_input("헤이딜러탁송")

    st.divider()

    # 실행 제어 버튼 그룹
    st.markdown("**🛠️ 실행 제어**")
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
    row2[5].button("내용리셋", type="secondary")

# --- [우측 섹션: 결과 출력] ---
with col_right:
    st.subheader("📝 결과 출력")
    st.markdown('<div class="output-box">', unsafe_allow_html=True)
    # 여기에 버튼 클릭 시나리오별 결과 출력 로직 추가 가능
    st.write("실행 결과가 여기에 표시됩니다.")
    st.markdown('</div>', unsafe_allow_html=True)
