from seobuk_251001A import run_pipeline

def execute_crawling(waiting_list, gcp_secrets, spreadsheet_name):
    """
    대기 중 작업 목록을 받은 후 크롤링을 실행하고 결과를 반환.

    Args:
        waiting_list (list): 작업 리스트 (sales_team, url, buyer)
        gcp_secrets (dict): GCP 인증 정보
        spreadsheet_name (str): 작업 대상 Google 스프레드시트 이름
    Returns:
        list: 완료된 작업의 결과 리스트
    """
    completed_tasks = []
    try:
        print("🔧 DEBUG: execute_crawling 시작...")  # 디버깅용 로그
        print(f"✅ waiting_list: {waiting_list},")
        print(f"✅ spreadsheet_name: {spreadsheet_name}")

        for task in waiting_list:
            url = task["url"]
            buyer = task["buyer"]
            sales_team = task["sales_team"]

            print(f"🔧 DEBUG: 현재 작업 - URL: {url}, Buyer: {buyer}, Sales팀: {sales_team}")

            # run_pipeline 호출 및 작업 실행
            list_pairs = [(url, buyer)]
            records = run_pipeline(
                list_pairs,
                user_name=sales_team,
                gcp_secrets=gcp_secrets,
                spreadsheet_name=spreadsheet_name,
                headless=True
            )

            if not records:  # records가 비어있다면 크롤링이 실패한 상태
                print(f"⚠️ WARNING: 작업 실패 (URL: {url}, Buyer: {buyer})")
            else:
                print(f"✅ 성공적으로 작업 완료된 records: {records}")
                completed_tasks.extend(records)  # 작업 완료 항목 추가

        print("🔧 DEBUG: execute_crawling 완료")
        return completed_tasks
    except Exception as e:
        print(f"❌ execute_crawling 오류 발생: {str(e)}")
        return []
