from seobuk_251001A import run_pipeline

def execute_crawling(waiting_list, gcp_secrets, spreadsheet_name):
    """
    대기 중 작업 목록을 처리하고 run_pipeline 실행 확인용 디버깅 로그 추가.
    """
    try:
        print("🚀 DEBUG: execute_crawling 시작")
        print(f"✅ waiting_list: {waiting_list}")
        print(f"✅ spreadsheet_name: {spreadsheet_name}")
        print(f"✅ gcp_secrets 전달됨: {gcp_secrets['type']}")

        completed_tasks = []  # 완료된 작업을 보관
        for task in waiting_list:
            print(f"🔧 DEBUG: 작업 실행 - URL: {task['url']}, Buyer: {task['buyer']}, Sales팀: {task['sales_team']}")
            list_pairs = [(task["url"], task["buyer"])]  # URL 및 Buyer 정보 입력
            
            # run_pipeline 호출 및 결과 반환 확인
            try:
                records = run_pipeline(
                    list_pairs=list_pairs,
                    user_name=task["sales_team"],
                    gcp_secrets=gcp_secrets,
                    spreadsheet_name=spreadsheet_name,
                    headless=True
                )

                if not records:
                    print(f"⚠️ WARNING: run_pipeline에서 빈 결과 반환 - URL: {task['url']}, Buyer: {task['buyer']}")
                completed_tasks.extend(records)
            except Exception as e:
                print(f"❌ ERROR: run_pipeline 실행 중 오류 발생: {e}")

        print("🚀 DEBUG: execute_crawling 종료 - completed_tasks: {completed_tasks}")
        return completed_tasks

    except Exception as e:
        print(f"❌ ERROR in execute_crawling: {e}")
        return [][]
