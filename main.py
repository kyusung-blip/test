import streamlit as st
import importlib

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

# 페이지 상태 초기화
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "메인"  # 초기값 '메인'

# 사용자 정의 사이드 메뉴 구성
with st.sidebar:
    st.title("메뉴 선택")
    menu_items = {
        "메인": None,
        "차량 매입 관리": "pages.차량.차량_매입",
        "탁송 관리": "pages.탁송.탁송_관리"
    }

    for menu_name, module_path in menu_items.items():
        if st.button(menu_name):
            st.session_state["selected_page"] = module_path

# 메인 콘텐츠 영역
selected_page = st.session_state["selected_page"]
if not selected_page or selected_page == "메인":
    st.title("🌐 메인 페이지")
    st.write("이 페이지는 서북인터내셔널의 메인 화면입니다.")

elif selected_page:
    try:
        module = importlib.import_module(selected_page)  # 동적 모듈 불러오기
        if hasattr(module, "main"):
            module.main()  # 각 페이지의 main() 함수 실행
        else:
            st.error(f"{selected_page}에 'main()' 함수가 정의되어 있지 않습니다.")
    except ModuleNotFoundError:
        st.error(f"{selected_page} 모듈을 찾을 수 없습니다. 파일 구조를 확인하세요.")
