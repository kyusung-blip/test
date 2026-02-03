from seobuk_251001A import run_pipeline
import traceback
import logging
from urllib.parse import urlparse

# Configure logging only if not already configured
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    logging.info(f"[execute_crawling] 시작")
    logging.info(f"   - waiting_list 개수: {len(waiting_list)}")
    logging.info(f"   - gcp_secrets 타입: {type(gcp_secrets)}")
    logging.info(f"   - spreadsheet_name: {spreadsheet_name}")
    
    print(f"🚀 [DEBUG] execute_crawling 시작")
    print(f"   - waiting_list 개수: {len(waiting_list)}")
    print(f"   - gcp_secrets 존재 여부: {gcp_secrets is not None}")
    print(f"   - spreadsheet_name: {spreadsheet_name}")
    
    # Validate inputs
    if not waiting_list:
        logging.error("[execute_crawling] waiting_list가 비어있습니다")
        print(f"❌ [ERROR] waiting_list가 비어있습니다")
        return []
    
    if not gcp_secrets:
        logging.error("[execute_crawling] gcp_secrets가 비어있습니다")
        print(f"❌ [ERROR] gcp_secrets가 비어있습니다")
        return []
    
    if not spreadsheet_name:
        logging.error("[execute_crawling] spreadsheet_name이 비어있습니다")
        print(f"❌ [ERROR] spreadsheet_name이 비어있습니다")
        return []
    
    completed_tasks = []

    for idx, task in enumerate(waiting_list):
        try:
            logging.info(f"[execute_crawling] 작업 {idx+1}/{len(waiting_list)} 처리 중")
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
                logging.error(f"[execute_crawling] {error_msg}")
                print(f"❌ [ERROR] {error_msg}")
                completed_tasks.append({
                    "url": task.get("url", "N/A"),
                    "buyer": task.get("buyer", "N/A"),
                    "status": "FAILED",
                    "error": error_msg
                })
                continue
            
            # Validate URL format (use local variable to avoid mutating input)
            url = task["url"].strip()
            
            try:
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    error_msg = "유효하지 않은 URL 형식입니다 (도메인이 없거나 프로토콜이 누락됨)"
                    logging.error(f"[execute_crawling] {error_msg}: {url}")
                    print(f"❌ [ERROR] {error_msg}: {url}")
                    completed_tasks.append({
                        "url": url,
                        "buyer": task.get("buyer", "N/A"),
                        "status": "FAILED",
                        "error": error_msg
                    })
                    continue
                if parsed_url.scheme not in ("http", "https"):
                    error_msg = "URL은 http:// 또는 https://로 시작해야 합니다"
                    logging.error(f"[execute_crawling] {error_msg}: {url}")
                    print(f"❌ [ERROR] {error_msg}: {url}")
                    completed_tasks.append({
                        "url": url,
                        "buyer": task.get("buyer", "N/A"),
                        "status": "FAILED",
                        "error": error_msg
                    })
                    continue
            except Exception as e:
                error_msg = f"URL 파싱 실패: {str(e)}"
                logging.error(f"[execute_crawling] {error_msg}")
                print(f"❌ [ERROR] {error_msg}")
                completed_tasks.append({
                    "url": url,
                    "buyer": task.get("buyer", "N/A"),
                    "status": "FAILED",
                    "error": error_msg
                })
                continue
            
            # Use cleaned URL for crawling
            list_pairs = [(url, task["buyer"])]
            logging.info(f"[execute_crawling] run_pipeline 호출 중...")
            print(f"   - run_pipeline 호출 중...")
            records = run_pipeline(
                list_pairs=list_pairs,
                user_name=task["sales_team"],
                gcp_secrets=gcp_secrets,
                spreadsheet_name=spreadsheet_name,
                headless=True
            )
            logging.info(f"[execute_crawling] run_pipeline 반환값: {records}")
            print(f"   - run_pipeline 반환값: {records}")
            
            if records:
                completed_tasks.extend(records)
                logging.info(f"[execute_crawling] 작업 성공 - {len(records)}개 레코드 추가")
                print(f"✅ [DEBUG] 작업 성공 - {len(records)}개 레코드 추가")
            else:
                logging.warning("[execute_crawling] run_pipeline이 빈 리스트 반환")
                print(f"⚠️  [WARNING] run_pipeline이 빈 리스트 반환")
                completed_tasks.append({
                    "url": task["url"],
                    "buyer": task["buyer"],
                    "status": "FAILED",
                    "error": "크롤링 결과가 없습니다"
                })
        except Exception as e:
            error_msg = f"작업 실패: {str(e)}"
            logging.error(f"[execute_crawling] {error_msg}")
            logging.error(traceback.format_exc())
            print(f"❌ [ERROR] {error_msg}")
            print(traceback.format_exc())
            completed_tasks.append({
                "url": task.get("url", "N/A"),
                "buyer": task.get("buyer", "N/A"),
                "status": "FAILED",
                "error": str(e)
            })
    
    logging.info(f"[execute_crawling] 종료 - 총 처리된 작업: {len(completed_tasks)}")
    print(f"\n🚀 [DEBUG] execute_crawling 종료")
    print(f"   - 총 처리된 작업: {len(completed_tasks)}")
    print(f"   - completed_tasks: {completed_tasks}")
    return completed_tasks
