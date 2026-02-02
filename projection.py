from seobuk_251001A import run_pipeline

def execute_crawling(waiting_list, gcp_secrets, spreadsheet_name):
    """
    대기 중 작업 목록을 받은 후 크롤링을 실행하고 결과를 반환.

    Args:
        waiting_list (list): 대기 중 작업 리스트 (sales_team, url, buyer)
        gcp_secrets (dict): 선택된 GCP Service Account 비밀 정보
        spreadsheet_name (str): 현재 작업에 사용할 스프레드시트 이름
    Returns:
        list: 완료된 작업 정보 리스트
    """
    completed_tasks = []
    try:
        for task in waiting_list:
            url = task["url"]
            buyer = task["buyer"]
            sales_team = task["sales_team"]

            # 크롤링 작업 수행을 위한 URL-Buyer 페어 생성
            list_pairs = [(url, buyer)]
            
            # GCP secrets와 선택된 스프레드시트를 run_pipeline 함수로 전달
            records = run_pipeline(
                list_pairs, 
                user_name=sales_team,  # 실행 사용자 정보 전달
                gcp_secrets=gcp_secrets,  # GCP 인증 정보 전달
                spreadsheet_name=spreadsheet_name,  # 현재 작업에 사용할 스프레드시트 이름 전달
                headless=True  # headless 모드 사용
            )
            completed_tasks.extend(records)  # 완료된 작업 정보 병합

        return completed_tasks
    except Exception as e:
        # 작업 실패 시 예외 메시지를 출력하고 빈 리스트 반환
        print(f"크롤링 실패: {e}")
        return []
