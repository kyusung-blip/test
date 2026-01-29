import streamlit as st

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

st.title("🌐 서북인터내셔널 업무 포털")
st.write("진행하실 업무를 선택해주세요.")

st.divider()

# 큰 버튼 배치를 위해 컬럼 나누기
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚗 차량 매입 관리")
    if st.button("Buy Program 실행", use_container_width=True, type="primary"):
        st.switch_page("pages/1_buyprogram.py")
    st.write("차량 정보 등록, 구글 시트 연동, 딜러 계좌 확인 등을 수행합니다.")

with col2:
    st.subheader("🚛 탁송 관리")
    if st.button("탁송 프로그램 실행", use_container_width=True):
        st.switch_page("pages/tak.py")
    st.write("출발지/도착지 설정 및 탁송 기사용 정보 추출을 수행합니다.")

st.divider()

st.info("💡 왼쪽 사이드바 메뉴를 통해서도 자유롭게 페이지 이동이 가능합니다.")

