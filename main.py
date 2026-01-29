import streamlit as st
import importlib


# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

# 페이지 상태 초기화
if "selected_menu" not in st.session_state:
    st.session_state["selected_menu"] = "메인"  # 기본 메뉴는 '메인'

# 왼쪽 사이드 메뉴 구성
with st.sidebar:
    st.title("메뉴")  # 사이드바 제목
    menu_items = ["메인", "차량 매입 관리", "탁송 관리", "프로젝션"]
    for item in menu_items:
        if st.button(item):
            st.session_state["selected_menu"] = item  # 선택한 메뉴 업데이트

# 메인 화면 구성
selected_menu = st.session_state["selected_menu"]
if selected_menu == "메인":
    st.title("🌐 서북인터내셔널 관리 시스템")
    st.write("이 페이지는 메인 페이지입니다. 메뉴를 선택하세요.")

elif selected_menu == "차량 매입 관리":
    st.title("🚗 차량 매입 관리")
    st.write("이 페이지는 차량 매입 관리를 위한 기능을 제공합니다.")
    # 차량 매입 관리 로직 추가 가능

elif selected_menu == "탁송 관리":
    st.title("🚛 탁송 관리")
    try:
        module = importlib.import_module("pages.delivery_management")
        if hasattr(module, "main"):
            module.main()
        else:
            st.error("탁송 관리 페이지에 'main()' 함수가 정의되어 있지 않습니다.")
    except Exception as e:
        st.error(f"오류 발생: {e}")

elif selected_menu == "프로젝션":
    st.title("📈 프로젝션")
    st.write("데이터 프로젝션 기능을 여기에서 구현할 수 있습니다.")
    number = st.number_input("프로젝션 값 입력", min_value=0, max_value=100, value=50)
    st.write(f"입력된 값: {number}")
    st.line_chart([number, number * 2, number * 3])  # 간단한 예제 차트
