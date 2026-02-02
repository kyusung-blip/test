import streamlit as st
from projection import execute_crawling  # projection.py에서 크롤링 함수 임포트

# 페이지 설정
st.set_page_config(page_title="프로젝션 관리", layout="wide")

# 상태 관리 초기화
if "progress_logs" not in st.session_state:
    st.session_state["progress_logs"] = []  # 진행 상태의 로그 저장
if "waiting_list" not in st.session_state:
    st.session_state["waiting_list"] = []  # 대기 중 리스트
if "in_progress" not in st.session_state:
    st.session_state["in_progress"] = []  # 진행 중 리스트
if "completed_list" not in st.session_state:
    st.session_state["completed_list"] = []  # 완료된 리스트

# Service Account 및 스프레드시트 동적 로드 함수
def load_secrets(account_type):
    """Streamlit Secrets에서 선택된 GCP 계정을 동적으로 로드"""
    try:
        account_secrets = st.secrets[account_type]
        return account_secrets
    except KeyError:
        st.error(f"[{account_type}]에 대한 정보가 없습니다.")
        return None

# GCP Service Account 선택
account_type = st.sidebar.selectbox(
    "GCP Service Account 선택", ["gcp_service_account_seobuk", "gcp_service_account_concise"]
)

# 선택된 계정의 secrets 가져오기
secrets = load_secrets(account_type)

# 스프레드시트 선택
if secrets is not None:
    st.sidebar.markdown("### 스프레드시트 선택")
    spreadsheet_names = secrets["spreadsheet_name"]
    selected_sheet = st.sidebar.selectbox("스프레드시트를 선택하세요", spreadsheet_names)

# 상단 구성
st.markdown("### Sales팀: 프로젝션 관리")
with st.container():
    col1, col2, col3, col4 = st.columns([2, 6, 2, 2])  # 비율 구성

    sales_team = st.selectbox("🚀 Sales팀 선택", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"], key="selected_sales")
    url = st.text_input("🌐 URL 입력", placeholder="예: https://example.com")
    buyer = st.text_input("🛒 Buyer 이름 입력", placeholder="예: John Doe")
    
    if st.button("저장"):
        if url and buyer:
            st.session_state["waiting_list"].append({"sales_team": sales_team, "url": url, "buyer": buyer})
            st.success(f"✅ 대기 중 리스트에 저장 완료: {buyer} - {url}")
        else:
            st.error("❌ URL과 Buyer 이름을 모두 입력해주세요!")

# 중단 구성: 진행 상태 모니터링
st.markdown("### 진행 상태")
with st.container():
    if len(st.session_state["progress_logs"]) > 0:
        for log in st.session_state["progress_logs"]:
            st.info(f"🔄 {log}")
    else:
        st.write("현재 진행 상태가 없습니다.")

# 하단 구성: 탭으로 나누기
st.markdown("### 작업 리스트")
tab1, tab2, tab3 = st.tabs(["⏳ 대기 중", "🚀 진행 중", "✅ 완료"])

# 대기중 탭
with tab1:
    st.write("📋 대기 중 리스트")
    if len(st.session_state["waiting_list"]) == 0:
        st.write("대기 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["waiting_list"]):
            st.write(f"{idx + 1}. 팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
            if st.button(f"작업 실행 {idx + 1}", key=f"start_{idx}"):
                # 작업 실행 ���튼 클릭 시 크롤링 시작
                st.session_state["progress_logs"].append(f"🔄 {item['buyer']} 작업 실행 중...")
                
                with st.spinner(f"{item['buyer']} 작업 처리 중..."):
                    waiting_items = [item]  # 단일 작업을 실행하도록 전달
                    completed = execute_crawling(waiting_items, secrets, selected_sheet)  # 크롤링 로직 호출

                    # 작업 상태 업데이트
                    st.session_state["in_progress"].append(item)  # 진행 중 목록에 추가
                    del st.session_state["waiting_list"][idx]  # 대기 중에서 제거
                    
                    # 완료된 작업 등록
                    st.session_state["completed_list"].extend(completed)
                    st.session_state["progress_logs"].append(f"✅ {item['buyer']} 작업 완료됨!")

# 진행중 탭
with tab2:
    st.write("📋 진행 중 리스트")
    if len(st.session_state["in_progress"]) == 0:
        st.write("현재 진행 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["in_progress"]):
            st.write(f"{idx + 1}. 팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
            if st.button(f"작업 완료 {idx + 1}", key=f"complete_{idx}"):
                st.session_state["completed_list"].append(item)
                del st.session_state["in_progress"][idx]
                st.session_state["progress_logs"].append(f"✅ {item['buyer']} 작업 완료됨!")

# 완료 탭
with tab3:
    st.write("📋 완료된 리스트")
    if len(st.session_state["completed_list"]) == 0:
        st.write("완료된 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["completed_list"]):
            st.write(f"{idx + 1}. 팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
