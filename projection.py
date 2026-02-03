from seobuk_251001A import run_pipeline
import traceback

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
    print(f"🚀 [DEBUG] execute_crawling 시작")
    print(f"   - waiting_list 개수: {len(waiting_list)}")
    print(f"   - gcp_secrets 존재 여부: {gcp_secrets is not None}")
    print(f"   - spreadsheet_name: {spreadsheet_name}")
    completed_tasks = []

    for idx, task in enumerate(waiting_list):
        try:
            print(f"\n🚀 [DEBUG] 작업 {idx+1}/{len(waiting_list)} 처리 중")
            print(f"   - URL: {task.get('url', 'N/A')}")
            print(f"   - Buyer: {task.get('buyer', 'N/A')}")
            print(f"   - Sales팀: {task.get('sales_team', 'N/A')}")
            
            # Validate inputs
            missing_fields = []
            if not task.get("url"):
                missing_fields.append("URL")
            if not task.get("buyer"):
                missing_fields.append("Buyer")
            
            if missing_fields:
                error_msg = f"{', '.join(missing_fields)}가 없습니다"
                print(f"❌ [ERROR] {error_msg}")
                completed_tasks.append({
                    "url": task.get("url", "N/A"),
                    "buyer": task.get("buyer", "N/A"),
                    "status": "FAILED",
                    "error": error_msg
                })
                continue
            
            list_pairs = [(task["url"], task["buyer"])]
            print(f"   - run_pipeline 호출 중...")
            records = run_pipeline(
                list_pairs=list_pairs,
                user_name=task["sales_team"],
                gcp_secrets=gcp_secrets,
                spreadsheet_name=spreadsheet_name,
                headless=True
            )
            print(f"   - run_pipeline 반환값: {records}")
            
            if records:
                completed_tasks.extend(records)
                print(f"✅ [DEBUG] 작업 성공 - {len(records)}개 레코드 추가")
            else:
                print(f"⚠️  [WARNING] run_pipeline이 빈 리스트 반환")
                completed_tasks.append({
                    "url": task["url"],
                    "buyer": task["buyer"],
                    "status": "FAILED",
                    "error": "크롤링 결과가 없습니다"
                })
        except Exception as e:
            print(f"❌ [ERROR] 작업 실패: {str(e)}")
            print(traceback.format_exc())
            completed_tasks.append({
                "url": task.get("url", "N/A"),
                "buyer": task.get("buyer", "N/A"),
                "status": "FAILED",
                "error": str(e)
            })
    
    print(f"\n🚀 [DEBUG] execute_crawling 종료")
    print(f"   - 총 처리된 작업: {len(completed_tasks)}")
    print(f"   - completed_tasks: {completed_tasks}")
    return completed_tasks
