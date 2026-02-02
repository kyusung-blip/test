import streamlit as st
from projection import execute_crawling  # projection.py에서 크롤링 함수 임포트

# 페이지 설정
st.set_page_config(page_title="프로젝션 관리", layout="wide")

# 세션 상태 초기화
if "progress_logs" not in st.session_state:
    st.session_state["progress_logs"] = []  # 진행 상태 로그 저장
if "waiting_list" not in st.session_state:
    st.session_state["waiting_list"] = []  # 대기 중 작업 리스트
if "in_progress" not in st.session_state:
    st.session_state["in_progress"] = []  # 진행 중 작업 리스트
if "completed_list" not in st.session_state:
    st.session_state["completed_list"] = []  # 완료된 작업 리스트

# Google Sheets와 관련된 설정
def load_secrets(account_type):
    """Streamlit Secrets에서 선택된 GCP 계정을 로드"""
    try:
        return st.secrets[account_type]
    except KeyError:
        st.error(f"[{account_type}]에 대한 정보가 없습니다.")
        return None

# GCP Service Account 선택
account_type = st.sidebar.selectbox(
    "GCP Service Account 선택", ["gcp_service_account_seobuk", "gcp_service_account_concise"]
)
secrets = load_secrets(account_type)  # secrets 로드
if secrets:
    spreadsheet_names = secrets["spreadsheet_name"]
    selected_sheet = st.sidebar.selectbox("스프레드시트를 선택하세요", spreadsheet_names)

# 상단 UI 구성
st.markdown("### Sales팀: 프로젝션 관리")
sales_team = st.selectbox("🚀 Sales팀 선택", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"])
url = st.text_input("🌐 URL 입력", placeholder="예: https://example.com")
buyer = st.text_input("🛒 Buyer 이름 입력", placeholder="예: John Doe")

if st.button("저장"):
    if url and buyer:
        st.session_state["waiting_list"].append({"sales_team": sales_team, "url": url, "buyer": buyer})
        st.success(f"✅ 대기 중 리스트에 저장 완료: Buyer={buyer}, URL={url}")
    else:
        st.error("❌ URL과 Buyer 이름을 모두 입력해주세요!")

# 작업 리스트 및 진행 상태
st.markdown("### 작업 리스트")
tab1, tab2, tab3 = st.tabs(["⏳ 대기 중", "🚀 진행 중", "✅ 완료"])

# 작업 실행 버튼
with tab1:
    st.write("📋 대기 중 작업 리스트")
    if not st.session_state["waiting_list"]:
        st.info("현재 대기 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["waiting_list"]):
            st.write(f"{idx + 1}. Sales팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
            if st.button(f"작업 실행: {idx + 1}", key=f"start_{idx}"):
                print(f"🚀 Streamlit 작업 실행 버튼 클릭 - Item: {item}")
                
                with st.spinner(f"🔄 {item['buyer']} 작업 실행 중..."):
                    completed_task = execute_crawling(
                        [item],  # 작업 리스트
                        secrets,  # GCP 인증 정보
                        selected_sheet  # 선택된 스프레드시트
                    )
                    
                    # 반환값 확인
                    print(f"✅ DEBUG: completed_task 반환값: {completed_task}")

                    # Streamlit에 반환값 표시
                    if completed_task:
                        st.session_state["completed_list"].extend(completed_task)
                        st.success(f"{item['buyer']} 작업 완료! 반환값: {completed_task}")
                    else:
                        st.error(f"{item['buyer']} 작업 실패! 반환값이 비어있음.")

                print(f"✅ Streamlit 작업 완료 - {item['buyer']}")

# 진행 중 작업 탭
with tab2:
    st.write("📋 진행 중 작업")
    if not st.session_state["in_progress"]:
        st.info("현재 진행 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["in_progress"]):
            st.write(f"작업 중: {item['buyer']}")

# 완료된 작업 탭
with tab3:
    st.write("📋 완료된 작업")
    if not st.session_state["completed_list"]:
        st.info("완료된 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["completed_list"]):
            st.write(f"{idx + 1}. 완료됨: {item['buyer']}")

# 로그 출력
st.markdown("### 작업 로그")
if st.session_state["progress_logs"]:
    for log in st.session_state["progress_logs"]:
        st.write(log)
else:
    st.info("현재 작업 로그가 없습니다.")
