import streamlit as st

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

st.title("🌐 서북인터내셔널 업무 포털")
st.write("진행하실 업무를 선택해주세요.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🚗 차량 매입 관리")
    if st.button("Buy Program 실행", use_container_width=True):
        st.experimental_set_query_params(page="buy_management")

with col2:
    st.subheader("🚛 탁송 관리")
    if st.button("탁송 프로그램 실행", use_container_width=True):
        st.experimental_set_query_params(page="delivery_management")

st.divider()
st.info("💡 위 버튼을 클릭하면 특정 페이지로 전환됩니다.")

# Query Parameter로 페이지 전환 로직
query_params = st.experimental_get_query_params()
page = query_params.get("page", [""])[0]

if page == "buy_management":
    st.write("🚗 차량 매입 관리 페이지입니다.")
elif page == "delivery_management":
    st.write("🚛 탁송 관리 페이지입니다.")
else:
    st.write("메인 페이지에 있습니다.")
