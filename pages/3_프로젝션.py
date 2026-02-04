import streamlit as st
from github import Github
import json
import uuid
from datetime import datetime
import time

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="프로젝션 관리", layout="wide")

# --- 2. GitHub 설정 (Secrets 활용) ---
try:
    ACCESS_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = "kyusung-blip/test" 
    g = Github(ACCESS_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    st.error(f"GitHub 설정 오류: {e}")
    st.stop()

# --- 3. [Fragment] 작업 현황 영역만 별도로 새로고침하는 함수 ---
@st.fragment(run_every="10s")  # 10초마다 이 함수 내부만 다시 실행됨
def show_status_board():
    st.subheader("📋 실시간 작업 현황 (10초 자동 갱신)")
    tab1, tab2 = st.tabs(["⏳ 진행 중 / 대기", "✅ 완료 목록"])

    try:
        # GitHub에서 최신 데이터 로드
        contents = repo.get_contents("data.json")
        data = json.loads(contents.decoded_content.decode("utf-8"))
        all_jobs = data.get("jobs", [])[::-1] 

        with tab1:
            processing_jobs = [j for j in all_jobs if j["status"] in ["waiting", "processing"]]
            if not processing_jobs:
                st.info("현재 대기 중인 작업이 없습니다.")
            for job in processing_jobs:
                user = job.get("user", "User")
                first_buyer = job.get("buyers", "").splitlines()[0] if job.get("buyers") else "Unknown"
                first_url = job.get("links", "").splitlines()[0] if job.get("links") else ""
                url_short = first_url[:30] + "..." if len(first_url) > 30 else first_url
                
                title_text = f"{user} / {first_buyer} / {url_short}"
                status_emoji = "🔵 대기" if job["status"] == "waiting" else "🟠 실행중"
                
                col_info, col_btn = st.columns([0.85, 0.15])
                with col_info:
                    with st.expander(f"{status_emoji} | {title_text}"):
                        st.caption(f"ID: {job['job_id']} | 등록: {job['created_at']}")
                        st.text(f"대상 URL:\n{job['links']}")
                with col_btn:
                    if job["status"] == "waiting":
                        # Fragment 내부의 버튼 클릭은 Fragment만 다시 돌게 하거나 
                        # 필요 시 전체 rerun을 유도할 수 있음
                        if st.button("취소", key=f"can_{job['job_id']}"):
                            latest = repo.get_contents("data.json")
                            l_data = json.loads(latest.decoded_content.decode("utf-8"))
                            l_data["jobs"] = [j for j in l_data["jobs"] if j["job_id"] != job["job_id"]]
                            repo.update_file(latest.path, f"Cancel {job['job_id']}", 
                                             json.dumps(l_data, ensure_ascii=False, indent=2), latest.sha)
                            st.toast("취소 완료")
                            st.rerun()

        with tab2:
            completed_jobs = [j for j in all_jobs if j["status"] == "completed"][:20]
            if not completed_jobs:
                st.write("완료된 내역이 없습니다.")
            for job in completed_jobs:
                user = job.get("user", "User")
                buyer = job.get("buyers", "").splitlines()[0] if job.get("buyers") else ""
                st.success(f"✅ {user} / {buyer} - 완료 ({job.get('completed_at', '')})")

    except Exception as e:
        st.write("데이터 업데이트 대기 중...")

# --- 4. 메인 화면 구성 ---
def main():
    st.title("📊 프로젝션 관리")

    # [상단 영역] 입력 폼: 이 부분은 10초 새로고침의 영향을 받지 않음
    with st.form("crawling_form", clear_on_submit=True):
        st.subheader("🤖 새 작업 추가")
        col1, col2 = st.columns(2)
        with col1:
            selected_user = st.selectbox("세일즈팀 (User)", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"])
        with col2:
            selected_hd_id = st.selectbox("HEYDEALER ID", ["seobuk", "inter77", "leeks21"])

        links = st.text_area("URLs (줄 바꿈으로 구분)", height=100)
        buyers = st.text_area("Buyer Names (줄 바꿈으로 구분)", height=100)
        submitted = st.form_submit_button("🚀 작업 등록 및 실행")

    if submitted:
        if not links or not buyers:
            st.error("데이터를 입력해주세요.")
        else:
            with st.spinner("GitHub 등록 중..."):
                try:
                    contents = repo.get_contents("data.json")
                    current_data = json.loads(contents.decoded_content.decode("utf-8"))
                    if "jobs" not in current_data: current_data["jobs"] = []

                    new_job = {
                        "job_id": str(uuid.uuid4())[:8],
                        "user": selected_user,
                        "hd_id": selected_hd_id,
                        "links": links.strip(),
                        "buyers": buyers.strip(),
                        "status": "waiting",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    current_data["jobs"].append(new_job)
                    repo.update_file(contents.path, f"Add Job {new_job['job_id']}", 
                                     json.dumps(current_data, ensure_ascii=False, indent=2), contents.sha)
                    
                    # Workflow 트리거
                    workflow = repo.get_workflow("main.yml")
                    workflow.create_dispatch("main")
                    st.success("✅ 등록 성공!")
                    time.sleep(1)
                    st.rerun() # 등록 시에는 전체 새로고침하여 폼을 비움
                except Exception as e:
                    st.error(f"등록 실패: {e}")

    st.divider()

    # [하단 영역] Fragment 함수 호출
    # 이 부분만 run_every 주기에 맞춰 독립적으로 돌아감
    show_status_board()

if __name__ == "__main__":
    main()
