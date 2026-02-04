import sys
import io

# 터미널 출력 인코딩을 UTF-8로 고정 (이 코드를 파일 맨 위에 넣으세요)
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

import json
import os
import seobuk_251001A as En

def run_local_task():
    # 1. Streamlit이 저장한 data.json 읽기
    if not os.path.exists("data.json"):
        print("Error: data.json 파일을 찾을 수 없습니다.")
        return

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. 데이터 파싱 (기존 MyThread.run 로직)
    list_links = [line.strip() for line in data["links"].splitlines() if line.strip()]
    list_buyers = [line.strip() for line in data["buyers"].splitlines() if line.strip()]
    list_pairs = list(zip(list_links, list_buyers))

    selected_user = data["selected_user"]
    selected_hd_id = data["selected_hd_id"]

    print(f"Start Task: {selected_user} / HD ID: {selected_hd_id}")
    print(f"작업 개수: {len(list_pairs)}개")

    print(f"--- 작업 시작 ({selected_user}) ---")
    total = len(list_pairs)
    
    for i, (url, buyer) in enumerate(list_pairs, 1):
        print(f"[{i}/{total}] 처리 중: {url[:30]}... (Buyer: {buyer})")
        # 한 개씩 처리되는 걸 확인하기 위해 루프 안에 로직을 넣거나
        # run_pipeline 내부의 print문을 활용하세요.

    try:
        En.run_pipeline(
            list_pairs=list_pairs, 
            user_name=selected_user, 
            headless=False, # 창이 뜨는 걸 보고 싶다면 False
            hd_login_id=selected_hd_id
        )
        print("--- 모든 작업 완료! 구글 시트를 확인하세요. ---")
    except Exception as e:
        print(f"--- 에러 발생: {e} ---")

if __name__ == "__main__":
    run_local_task()
