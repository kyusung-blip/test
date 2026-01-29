import streamlit as st

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

# 페이지 상태 초기화
if "selected_menu" not in st.session_state:
    st.session_state["selected_menu"] = "메인"  # 초기값으로 '메인' 설정

# 사이드바 구성
with st.sidebar:
    st.title("서북인터내셔널")
    st.write("메뉴를 선택하세요:")
    menu_items = ["메인", "차량 매입 관리", "탁송 관리", "프로젝션"]  # 메뉴 리스트 정의
    # 버튼 생성 및 상태 업데이트
    for item in menu_items:
        if st.button(item):  # 클릭한 버튼에 따라 상태 변경
            st.session_state["selected_menu"] = item  # 선택된 메뉴를 상태에 저장

# 선택된 메뉴에 따라 오른쪽 콘텐츠 영역 업데이트
selected_menu = st.session_state["selected_menu"]
if selected_menu == "메인":
    st.title("🌐 메인 페이지")
    st.write("이 페이지는 서북인터내셔널의 메인 화면입니다.")

elif selected_menu == "차량 매입 관리":
    st.title("🚗 차량 매입 관리")
    st.write("이 페이지는 차량 매입 관리를 위한 기능을 제공합니다.")

elif selected_menu == "탁송 관리":
    st.title("🚛 탁송 관리")
    st.write("이 페이지는 탁송 관리를 위한 기능을 제공합니다.")

elif selected_menu == "프로젝션":
    st.title("📈 프로젝션")
    st.write("이 페이지는 데이터 프로젝션을 위한 공간입니다.")
    value = st.number_input("입력 값을 설정하세요", min_value=0, max_value=100, value=50)
    st.write(f"입력된 값: {value}")
    st.line_chart([value * i for i in range(1, 5)])  # 간단한 예제 차트
