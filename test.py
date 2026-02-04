import json
import os
import sys
import io
from datetime import datetime
from github import Github
import seobuk_251001A as En

# 터미널 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

# --- GitHub 설정 (본인 토큰 입력) ---
ACCESS_TOKEN = os.getenv("MY_GITHUB_TOKEN")
REPO_NAME = "kyusung-blip/test"

def run_local_task():
    print(f"[{datetime.now()}] 작업 큐 확인 중...")
    
    g = Github(ACCESS_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    # 1. GitHub에서 데이터 가져오기
    contents = repo.get_contents("data.json")
    data = json.loads(contents.decoded_content.decode("utf-8"))

    # 2. 'waiting' 상태인 작업 찾기
    jobs = data.get("jobs", [])
    target_job = next((j for j in jobs if j["status"] == "waiting"), None)

    if not target_job:
        print("대기 중인 작업이 없습니다.")
        return

    job_id = target_job["job_id"]
    print(f"🚀 작업 시작: JOB #{job_id}")

    # 3. 상태를 'processing'으로 변경
    target_job["status"] = "processing"
    repo.update_file(contents.path, f"Processing {job_id}", 
                     json.dumps(data, ensure_ascii=False, indent=2), contents.sha)

    # 4. 데이터 파싱 (여기서 data["links"]를 쓰지 않습니다!)
    links_str = target_job.get("links", "")
    buyers_str = target_job.get("buyers", "")
    
    list_links = [line.strip() for line in links_str.splitlines() if line.strip()]
    list_buyers = [line.strip() for line in buyers_str.splitlines() if line.strip()]
    list_pairs = list(zip(list_links, list_buyers))

    # 5. 실행
    try:
        En.run_pipeline(
            list_pairs=list_pairs, 
            user_name=target_job["user"], 
            headless=True,
            hd_login_id=target_job["hd_id"]
        )
        
        # 6. 완료 업데이트
        contents = repo.get_contents("data.json")
        data = json.loads(contents.decoded_content.decode("utf-8"))
        for j in data["jobs"]:
            if j["job_id"] == job_id:
                j["status"] = "completed"
                j["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        repo.update_file(contents.path, f"Complete {job_id}", 
                         json.dumps(data, ensure_ascii=False, indent=2), contents.sha)
        print(f"✅ JOB #{job_id} 완료")
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    run_local_task()
