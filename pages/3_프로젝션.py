import streamlit as st
from github import Github
import json
import uuid
from datetime import datetime

def main():
    st.title("📊 프로젝션 관리")

    # --- 1. GitHub 설정 (Secrets 활용) ---
    try:
        ACCESS_TOKEN = st.secrets["GITHUB_TOKEN"]
        REPO_NAME = "kyusung-blip/test" # 본인의 저장소 경로로 수정
        g = Github(ACCESS_TOKEN)
        repo = g.get_repo(REPO_NAME)
    except Exception as e:
        st.error(f"GitHub 설정 오류: {e}")
        return

    # --- 2. 작업 입력 폼 ---
    with st.form("crawling_form"):
        st.subheader("🤖 새 작업 추가")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_user = st.selectbox("세일즈팀 (User)", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"])
        with col2:
            selected_hd_id = st.selectbox("HEYDEALER ID", ["seobuk", "inter77", "leeks21"])

        links = st.text_area("URLs (줄 바꿈으로 구분)", height=150)
        buyers = st.text_area("Buyer Names (줄 바꿈으로 구분)", height=150)

        submitted = st.form_submit_button("🚀 작업 큐에 추가 및 로컬 실행")

    # --- 3. 버튼 클릭 시 데이터 업데이트 및 실행 ---
    if submitted:
        if not links or not buyers:
            st.error("URL과 바이어 이름을 모두 입력해주세요.")
        else:
            with st.spinner("GitHub에 작업을 등록 중..."):
                try:
                    # 기존 data.json 불러오기
                    contents = repo.get_contents("data.json")
                    current_data = json.loads(contents.decoded_content.decode("utf-8"))
                    
                    # jobs 리스트가 없으면 초기화
                    if "jobs" not in current_data:
                        current_data["jobs"] = []

                    # 새 작업 생성
                    new_job = {
                        "job_id": str(uuid.uuid4())[:8],
                        "user": selected_user,
                        "hd_id": selected_hd_id,
                        "links": links.strip(),
                        "buyers": buyers.strip(),
                        "status": "waiting", # waiting -> processing -> completed
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    current_data["jobs"].append(new_job)

                    # GitHub에 파일 업데이트
                    repo.update_file(
                        contents.path, 
                        f"Add Job {new_job['job_id']}", 
                        json.dumps(current_data, ensure_ascii=False, indent=2), 
                        contents.sha
                    )
                    
                    # Workflow 트리거
                    workflow = repo.get_workflow("main.yml")
                    workflow.create_dispatch("main")
                    
                    st.success(f"✅ 작업 #{new_job['job_id']} 등록 완료! 로컬 PC가 곧 시작합니다.")
                except Exception as e:
                    st.error(f"작업 등록 실패: {e}")

    st.divider()

    # --- 4. 작업 상태 리스트 (탭 구성) ---
    st.subheader("📋 작업 현황")
    tab1, tab2 = st.tabs(["⏳ 진행 중 / 대기", "✅ 완료 목록"])

    try:
        # 최신 데이터 다시 불러오기
        contents = repo.get_contents("data.json")
        data = json.loads(contents.decoded_content.decode("utf-8"))
        all_jobs = data.get("jobs", [])[::-1] # 최신순 정렬

        with tab1:
            processing_jobs = [j for j in all_jobs if j["status"] in ["waiting", "processing"]]
            if not processing_jobs:
                st.write("진행 중인 작업이 없습니다.")
            for job in processing_jobs:
                status_color = "🔵 대기 중" if job["status"] == "waiting" else "🟠 실행 중"
                with st.expander(f"{status_color} | #{job['job_id']} - {job['user']} ({job['created_at']})"):
                    st.text(f"URL: {job['links']}")
                    st.text(f"Buyers: {job['buyers']}")

        with tab2:
            completed_jobs = [j for j in all_jobs if j["status"] == "completed"]
            if not completed_jobs:
                st.write("완료된 작업이 없습니다.")
            for job in completed_jobs:
                st.success(f"#{job['job_id']} | {job['user']} - 완료됨 ({job.get('completed_at', '시간 미상')})")

    except Exception as e:
        st.info("작업 현황을 불러오는 중입니다...")

if __name__ == "__main__":
    main()
