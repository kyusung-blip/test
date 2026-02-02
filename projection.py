from seobuk_251001A import run_pipeline

def execute_crawling(waiting_list, gcp_secrets, spreadsheet_name):
    """
    대기 중 작업 목록을 받은 후 크롤링을 실행하고 결과를 반환.
    Args:
        waiting_list (list): 대기 중 작업 리스트 (sales_team, url, buyer)
        gcp_secrets (dict): GCP Service Account 인증 정보
        spreadsheet_name (str): 작업 대상 Google 스프레드시트 이름
    Returns:
        list: 완료된 작업의 결과 리스트
    """
    print(f"🚀 [DEBUG] execute_crawling 시작 - waiting_list: {waiting_list}")
    completed_tasks = []

    for task in waiting_list:
        try:
            print(f"🚀 [DEBUG] 현재 작업 - URL: {task['url']}, Buyer: {task['buyer']}, Sales팀: {task['sales_team']}")
            list_pairs = [(task["url"], task["buyer"])]
            records = run_pipeline(
                list_pairs=list_pairs,
                user_name=task["sales_team"],
                gcp_secrets=gcp_secrets,
                spreadsheet_name=spreadsheet_name,
                headless=True
            )
            completed_tasks.extend(records)
        except Exception as e:
            print(f"❌ [ERROR] Crrawling 실패: {e}")
    
    print(f"🚀 [DEBUG] execute_crawling 종료 - completed_tasks: {completed_tasks}")
    return completed_tasks
