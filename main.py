import streamlit as st
import importlib

# --- 공통 초기화 함수 정의 ---
def initialize_session_state():
    """
    세션 상태를 초기화합니다. 모든 페이지에서 공통으로 사용하는 상태를 정의합니다.
    """
    default_states = {
        "selected_page": "메인",  # 기본 페이지 값
        "progress_logs": [],
        "waiting_list": [],
        "in_progress": [],
        "completed_list": []
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --- 페이지 초기화 ---
initialize_session_state()

# --- 사이드바 메뉴 ---
menu_items = {
    "메인": None,
    "차량 매입 관리": "pages.1_차량_매입_관리",
    "탑승 관리": "pages.2_탑승_관리",
    "프로젝션 관리": "pages.3_프로젝션",
    "데이터 매핑 관리": "pages.4_매핑_관리"
}

with st.sidebar:
    st.title("🔗 메뉴 선택")
    for menu_name, module_path in menu_items.items():
        if st.button(menu_name):
            st.session_state["selected_page"] = module_path or "메인"

# --- 선택된 페이지 처리 ---
selected_page = st.session_state["selected_page"]

if selected_page == "메인":
    # 메인 페이지
    st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")
    st.title("🌍 메인 페이지")
    st.write("이 페이지는 서북인터내셔널의 메인 화면입니다.")
else:
    # 모듈 로드 및 실행
    try:
        module = importlib.import_module(selected_page)  # 동적 모듈 불러오기
        if hasattr(module, "main"):
            module.main()  # 각 페이지의 main() 실행
        else:
            st.error(f"🔴 {selected_page}에 'main()' 함수가 정의되어 있지 않습니다.")
    except ModuleNotFoundError:
        st.error(f"🔴 {selected_page} 모듈을 찾을 수 없습니다. 파일 구조를 확인하세요.")

