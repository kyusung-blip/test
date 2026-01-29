import streamlit as st
import importlib


# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

# 페이지 상태를 관리하기 위한 초기화
if "selected_menu" not in st.session_state:
    st.session_state["selected_menu"] = "차량 매입 관리"  # 기본 메뉴

# 화면 구성: 왼쪽 메뉴 영역과 오른쪽 콘텐츠 영역
menu_col, content_col = st.columns([1, 4])  # 전체 화면 비율 20% : 80%

# 왼쪽 메뉴 (Vertical Menu)
with menu_col:
    st.image("https://via.placeholder.com/150x80", caption="서북인터내셔널", use_column_width=True)
    st.title("메뉴")  # 메뉴 제목
    menu_items = ["차량 매입 관리", "탁송 관리", "프로젝션"]
    for item in menu_items:
        if st.button(item, use_container_width=True):
            st.session_state["selected_menu"] = item

# 오른쪽 콘텐츠 영역
with content_col:
    selected_menu = st.session_state["selected_menu"]
    if selected_menu == "차량 매입 관리":
        st.title("🚗 차량 매입 관리")
        st.write("이 페이지는 차량 매입 관리를 위한 기능을 제공합니다.")
        # 차량 매입 관리의 구체적인 로직을 여기에 추가하세요 (예: 입력 필드, 처리 로직 등)

    elif selected_menu == "탁송 관리":
        st.title("🚛 탁송 관리")
        # 탁송 관리 모듈 불러오기
        try:
            module = importlib.import_module("pages.delivery_management")
            if hasattr(module, "main"):
                module.main()  # 페이지 메인 함수 실행
            else:
                st.error("탁송 관리 페이지에 'main()' 함수가 정의되어 있지 않습니다.")
        except Exception as e:
            st.error(f"탁송 관리 모듈을 불러오는 중 오류가 발생했습니다: {e}")
    
    elif selected_menu == "프로젝션":
        st.title("📈 프로젝션")
        st.write("이 페이지는 데이터 프로젝션을 위한 공간입니다.")
        # 프로젝션 관련 로직 추가 가능
