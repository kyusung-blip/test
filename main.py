import streamlit as st

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

st.title("🌐 서북인터내셔널 업무 포털")
st.write("진행하실 업무를 선택해주세요.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🚗 차량 매입 관리")
    if st.button("Buy Program 실행", use_container_width=True, type="primary"):
        st.switch_page("pages/1_차량_매입_관리.py")

with col2:
    st.subheader("🚛 탁송 관리")
    if st.button("탁송 프로그램 실행", use_container_width=True):
        st.switch_page("pages/2_탁송_관리.py")

st.divider()
