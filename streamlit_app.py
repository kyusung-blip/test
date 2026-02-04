import streamlit as st
from github import Github
import json

# --- 설정 (본인의 정보로 수정) ---
ACCESS_TOKEN = "여기에_발급받은_ghp_토큰"
REPO_NAME = "본인아이디/저장소이름"

st.set_page_config(page_title="Seobuk Crawling System", layout="wide")
st.title("🚗 Seobuk Crawling System (Remote)")

with st.form("crawling_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        selected_user = st.selectbox("세일즈팀 (User)", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"])
    with col2:
        selected_hd_id = st.selectbox("HEYDEALER ID", ["seobuk", "inter77", "leeks21"])

    st.info("URL과 바이어 이름을 줄 바꿈으로 구분하여 입력하세요 (1:1 매칭)")
    links = st.text_area("URLs (Encar, Heydealer, etc.)", height=200)
    buyers = st.text_area("Buyer Names", height=200)

    submitted = st.form_submit_with_button("정보 저장 및 로컬 실행 시작")

if submitted:
    if not links or not buyers:
        st.error("URL과 바이어 이름을 모두 입력해주세요.")
    else:
        # 데이터 정리
        data_to_send = {
            "selected_user": selected_user,
            "selected_hd_id": selected_hd_id,
            "links": links.strip(),
            "buyers": buyers.strip()
        }

        # 1. GitHub API 연결
        g = Github(ACCESS_TOKEN)
        repo = g.get_repo(REPO_NAME)

        # 2. data.json 파일 업데이트 (정보 전달용)
        try:
            contents = repo.get_contents("data.json")
            repo.update_file(contents.path, "Update info from Streamlit", json.dumps(data_to_send, ensure_ascii=False), contents.sha)
            
            # 3. GitHub Action 트리거 (로컬 PC 깨우기)
            workflow = repo.get_workflow("main.yml")
            workflow.create_dispatch("main")
            
            st.success(f"✅ 데이터가 저장되었습니다! 로컬 PC({selected_user} 환경)에서 크롤링이 곧 시작됩니다.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
