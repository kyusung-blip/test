import streamlit as st
import seobuk_251001A as En
from datetime import datetime
import time

# 1. 페이지 기본 설정 (PyQt의 setWindowTitle, setFixedSize 대응)
st.set_page_config(page_title="Crawling System", layout="centered")

# 2. 스타일 커스텀 (PyQt의 StyleSheet 대응)
st.markdown("""
    <style>
    .status-box {
        padding: 10px;
        border-radius: 5px;
        border: 1px solid black;
        text-align: center;
        margin-bottom: 20px;
    }
    .processing { background-color: lightgreen; }
    .completed { background-color: lightblue; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🕷️ Crawling System")
    st.caption("by SEOBUK")

    # 3. 사이드바 설정 (PyQt의 상단 드롭다운 메뉴들을 사이드바로 이동)
    with st.sidebar:
        st.header("Settings")
        
        # 사용자 선택 (QComboBox 대응)
        user_list = ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"]
        selected_user = st.selectbox("Select User", user_list)
        
        # 헤이딜러 ID 선택 (hd_dropdown 대응)
        hd_ids = list(En.HEYDEALER_ACCOUNTS.keys())
        selected_hd_id = st.selectbox("Select HD ID", hd_ids)

    # 4. 메인 입력 화면 (TextEdit 대응)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Links")
        text_links = st.text_area("한 줄에 하나씩 링크 입력", height=300, key="links")
        
    with col2:
        st.subheader("Buyers")
        text_buyers = st.text_area("한 줄에 하나씩 구매자 입력", height=300, key="buyers")

    # 5. 상태 표시 레이블 공간
    status_placeholder = st.empty()

    # 6. 버튼 영역 (pushButton_2, pushButton_3 대응)
    btn_col1, btn_col2 = st.columns([1, 1])
    
    with btn_col1:
        start_button = st.button("🚀 Search System", use_container_width=True)
        
    with btn_col2:
        reset_button = st.button("🔄 Reset", use_container_width=True)

    # 리셋 로직
    if reset_button:
        st.rerun()

    # 실행 로직 (MyThread의 run() 메서드 대응)
    if start_button:
        if not text_links or not text_buyers:
            st.warning("링크와 구매자 정보를 모두 입력해주세요.")
            return

        # 데이터 가공
        list_links = [line.strip() for line in text_links.splitlines() if line.strip()]
        list_buyers = [line.strip() for line in text_buyers.splitlines() if line.strip()]
        list_pairs = list(zip(list_links, list_buyers))

        # 진행 상태 표시 (Program Processing)
        status_placeholder.markdown(
            '<div class="status-box processing">Program Processing</div>', 
            unsafe_allow_html=True
        )

        try:
            # 실제 크롤링 함수 호출 (headless 옵션은 환경에 따라 조절)
            # 웹 배포 시에는 반드시 headless=True 여야 합니다.
            En.run_pipeline(list_pairs, selected_user, headless=True, hd_login_id=selected_hd_id)
            
            # 완료 표시 (Completed)
            now = datetime.now().strftime("%m/%d _ %H:%M:%S")
            status_placeholder.markdown(
                f'<div class="status-box completed">Completed {now}</div>', 
                unsafe_allow_html=True
            )
            st.balloons() # 시각적 효과
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
            status_placeholder.empty()

if __name__ == "__main__":
    main()
