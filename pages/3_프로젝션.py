# pages/3_프로젝션.py 파일 예시
import streamlit as st
from github import Github
import json

def main():
    st.title("프로젝션")
    
    # --- 설정 ---
    ACCESS_TOKEN = "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"
    REPO_NAME = "kyusung-blip/test"

    with st.form("crawling_form"):
        st.subheader("🤖 로컬 PC 원격 실행 설정")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_user = st.selectbox("세일즈팀 (User)", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"])
        with col2:
            selected_hd_id = st.selectbox("HEYDEALER ID", ["seobuk", "inter77", "leeks21"])

        links = st.text_area("URLs (줄 바꿈으로 구분)", height=150)
        buyers = st.text_area("Buyer Names (줄 바꿈으로 구분)", height=150)

        submitted = st.form_submit_with_button("🚀 로컬 PC에서 크롤링 시작")

    if submitted:
        if not links or not buyers:
            st.error("URL과 바이어 이름을 모두 입력해주세요.")
        else:
            data_to_send = {
                "selected_user": selected_user,
                "selected_hd_id": selected_hd_id,
                "links": links.strip(),
                "buyers": buyers.strip()
            }

            try:
                g = Github(ACCESS_TOKEN)
                repo = g.get_repo(REPO_NAME)
                
                # data.json 업데이트
                contents = repo.get_contents("data.json")
                repo.update_file(contents.path, "Update from Streamlit", json.dumps(data_to_send, ensure_ascii=False), contents.sha)
                
                # Workflow 트리거
                workflow = repo.get_workflow("main.yml")
                workflow.create_dispatch("main")
                
                st.success(f"✅ 명령 전달 완료! 로컬 PC의 터미널(Runner)을 확인하세요.")
            except Exception as e:
                st.error(f"GitHub 통신 오류: {e}")
# ... 기존 코드 생략 ...
            except Exception as e:
                st.error(f"GitHub 통신 오류: {e}")

# 👇 이 부분을 추가해야 화면이 그려집니다!
if __name__ == "__main__":
    main()
