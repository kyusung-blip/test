from seobuk_251001A import run_pipeline  # 크롤링 로직 가져오기

def execute_crawling(waiting_list):
    """
    대기 중 작업 목록을 받아 크롤링을 실행.
    Args:
        waiting_list (list): 대기 중 작업 리스트 (sales_team, url, buyer)
    Returns:
        dict: 완료된 작업 정보를 반���
    """
    completed_tasks = []
    try:
        for task in waiting_list:
            url = task["url"]
            buyer = task["buyer"]
            sales_team = task["sales_team"]
            
            list_pairs = [(url, buyer)]  # 크롤링 작업 리스트 생성
            records = run_pipeline(list_pairs, user_name=sales_team, headless=True)
            completed_tasks.extend(records)  # 완료된 작업 추가
            
        return completed_tasks
    except Exception as e:
        print(f"크롤링 실패: {e}")
        return []
