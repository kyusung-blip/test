from seobuk_251001A import run_pipeline

def execute_crawling(waiting_list, gcp_secrets, spreadsheet_name):
    """
    대기 중 작업 목록을 처리하고 run_pipeline으로 전달.
    """
    completed_tasks = []
    try:
        print("🚀 DEBUG: execute_crawling 시작")
        print(f"✅ waiting_list: {waiting_list}")
        print(f"✅ gcp_secrets: {gcp_secrets['type']} - 인증 정보 전달됨")  # gcp_secrets가 올바른지 간략 확인
        print(f"✅ spreadsheet_name: {spreadsheet_name}")

        for task in waiting_list:
            url = task["url"]
            buyer = task["buyer"]
            sales_team = task["sales_team"]

            print(f"🔧 DEBUG: 현재 작업 처리 시작 - URL: {url}, Buyer: {buyer}, Sales팀: {sales_team}")

            # URL과 Buyer 정보 전달
            list_pairs = [(url, buyer)]

            # run_pipeline 호출
            records = run_pipeline(
                list_pairs,
                user_name=sales_team,
                gcp_secrets=gcp_secrets,
                spreadsheet_name=spreadsheet_name,
                headless=True
            )

            print(f"🔧 DEBUG: run_pipeline 실행 후 반환값 - {records}")
            completed_tasks.extend(records)  # 처리된 결과 추가

        print("🚀 DEBUG: execute_crawling 완료")
        return completed_tasks

    except Exception as e:
        print(f"❌ ERROR in execute_crawling: {e}")
        return []
