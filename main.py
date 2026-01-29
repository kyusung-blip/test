import streamlit as st
import importlib

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

# 팝업 상태 변수 초기화
if "show_popup" not in st.session_state:
    st.session_state["show_popup"] = False

# 팝업 열기 버튼
def open_popup():
    st.session_state["show_popup"] = True

# 팝업 닫기 버튼
def close_popup():
    st.session_state["show_popup"] = False

# 메인 화면
st.title("🌐 서북인터내셔널 업무 포털")
st.write("진행하실 업무를 선택해주세요.")
st.divider()

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚗 차량 매입 관리")
        if st.button("차량 매입 관리 실행"):  # 예시 버튼
            st.write("차량 매입 관리 페이지 링크!")

    with col2:
        st.subheader("🚛 탁송 관리")
        if st.button("탁송 관리 실행"):
            open_popup()  # 팝업 상태 활성화

# 팝업 창 렌더링
if st.session_state["show_popup"]:
    with st.container():
        st.write("### 🚛 탁송 관리 팝업")
        # import를 통해 탁송 관리 로직 가져오기
        try:
            module = importlib.import_module("pages.2_탁송_관리")
            if hasattr(module, "main"):
                module.main()  # 탁송 관리 페이지 로딩
            else:
                st.error("탁송 관리 페이지에 'main()' 함수가 정의되어 있지 않습니다.")
        except Exception as e:
            st.error(f"페이지를 로드하는 중 오류가 발생했습니다: {e}")

        # 팝업 닫기 버튼
        if st.button("닫기"):
            close_popup()  # 팝업 상태 비활성화
