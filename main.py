import streamlit as st
import importlib

# 페이지 설정
st.set_page_config(page_title="서북인터내셔널 관리 시스템", layout="wide")

st.title("🌐 서북인터내셔널 업무 포털")
st.write("진행하실 업무를 선택해주세요.")
st.divider()

# 페이지 전환 함수 (importlib 이용)
def load_page(module_name):
    try:
        module = importlib.import_module(module_name)  # 동적 모듈 가져오기
        if hasattr(module, "main"):
            module.main()  # 각 파일에서 정의된 main() 함수 실행
        else:
            st.error(f"{module_name}에 'main()' 함수가 정의되어 있지 않습니다.")
    except ModuleNotFoundError:
        st.error(f"{module_name} 파일을 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"페이지를 로드하는 중 오류가 발생했습니다: {e}")

# 버튼 UI 내에서 다른 파일(main 진입점 호출) 불러오기
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚗 차량 매입 관리")
    if st.button("buyprogram"):
        load_page("pages.1_차량_매입_관리")  # 파일 이름: pages/car_management.py

with col2:
    st.subheader("🚛 탁송 관리")
    if st.button("탁송 관리 실행"):
        load_page("pages.2_탁송_관리")  # 파일 이름: pages/delivery_management.py
