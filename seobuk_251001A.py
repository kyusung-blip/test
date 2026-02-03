import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import warnings
import re
import traceback
import json
import logging

warnings.filterwarnings(action='ignore')

# Configure logging only if not already configured
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =========================
# 크롬 드라이버 생성
# =========================
def make_driver(headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("window-size=1920x1080")
    options.add_argument("disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(options=options)

# =========================
# Google Sheets 연결
# =========================
def convert_to_dict(obj):
    """
    객체를 일반 딕셔너리로 변환합니다.
    
    Args:
        obj: 변환할 객체 (dict, AttrDict, str 등)
    
    Returns:
        dict: 변환된 딕셔너리
    
    Raises:
        ValueError: 변환할 수 없는 타입인 경우
    """
    if obj is None:
        raise ValueError("Cannot convert None to dict")
    
    # Already a plain dict (not a subclass like AttrDict)
    if type(obj) == dict:
        return obj
    
    # String (JSON)
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {str(e)}")
    
    # AttrDict or dict-like object (has keys() and __getitem__)
    if hasattr(obj, 'keys') and hasattr(obj, '__getitem__'):
        try:
            result = {}
            for key in obj.keys():
                value = obj[key]
                # Recursively convert nested structures
                # convert_to_dict will handle plain dicts, AttrDicts, etc.
                if type(value) != dict and (hasattr(value, 'keys') and hasattr(value, '__getitem__')):
                    result[key] = convert_to_dict(value)
                else:
                    result[key] = value
            return result
        except Exception as e:
            raise ValueError(f"Failed to convert dict-like object: {str(e)}")
    
    raise ValueError(f"Cannot convert type {type(obj)} to dict")

def connect_to_google_sheet(gcp_secrets, spreadsheet_name):
    """
    GCP 인증 정보를 이용해 Google Sheets에 연결.

    Args:
        gcp_secrets (dict or str or AttrDict): GCP Service Account 인증 정보
                                   - dict: GCP Service Account JSON 키파일의 내용을 딕셔너리로 변환한 것
                                   - str: GCP Service Account JSON 키파일의 내용을 문자열로 직렬화한 것
                                         (예: '{"type": "service_account", "project_id": "...", ...}')
                                   - AttrDict: Streamlit secrets에서 반환되는 객체
        spreadsheet_name (str): 열고자 하는 스프레드시트 이름
                                (예: "SEOBUK PROJECTION" - ID: 139D1fskBpdGGbG2O7FQIQJJbwVmt2hPxqgFc-QXOAfY)
    Returns:
        gspread.Spreadsheet: 연결된 스프레드시트 객체
    """
    logging.info(f"[connect_to_google_sheet] 시작 - spreadsheet_name: {spreadsheet_name}")
    logging.info(f"[connect_to_google_sheet] gcp_secrets 타입: {type(gcp_secrets)}")
    
    # Validate and convert gcp_secrets to dict if necessary
    if gcp_secrets is None:
        logging.error("[connect_to_google_sheet] gcp_secrets가 None입니다")
        raise ValueError("GCP secrets cannot be None")
    
    # Convert to dict (handles str, dict, AttrDict, etc.)
    try:
        logging.info("[connect_to_google_sheet] gcp_secrets를 딕셔너리로 변환 중...")
        gcp_secrets = convert_to_dict(gcp_secrets)
        logging.info("[connect_to_google_sheet] 딕셔너리 변환 성공")
    except ValueError as e:
        logging.error(f"[connect_to_google_sheet] 딕셔너리 변환 실패: {str(e)}")
        raise ValueError(f"Failed to convert gcp_secrets to dict: {str(e)}")
    
    # Ensure gcp_secrets is a dictionary
    if not isinstance(gcp_secrets, dict):
        logging.error(f"[connect_to_google_sheet] gcp_secrets가 딕셔너리가 아닙니다: {type(gcp_secrets)}")
        raise TypeError(f"gcp_secrets must be a dict, got {type(gcp_secrets)}")
    
    # Define the required scopes for Google Sheets and Drive access
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        logging.info("[connect_to_google_sheet] ServiceAccountCredentials 생성 중...")
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secrets, scopes=scopes)
        logging.info("[connect_to_google_sheet] 인증 정보 생성 완료")
        
        gc = gspread.authorize(credentials)
        logging.info("[connect_to_google_sheet] gspread 인증 완료")
        
        # Google 스프레드시트 열기
        spreadsheet = gc.open(spreadsheet_name)
        logging.info(f"✅ {spreadsheet_name} 스프레드시트 열림")
        print(f"✅ {spreadsheet_name} 스프레드시트 열림")
        return spreadsheet
    except Exception as e:
        logging.error(f"[connect_to_google_sheet] 스프레드시트 연결 실패: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"⛔️ 스프레드시트를 열 수 없습니다: {e}")
        return None

# =========================
# 크롤링 작업: URL 당 결과 처리
# =========================
def process_url(driver, url, buyer):
    """
    단일 URL과 Buyer에 대한 크롤링 작업 수행.
    """
    print(f"\n🚀 [DEBUG] process_url 시작")
    print(f"   - URL: {url}")
    print(f"   - Buyer: {buyer}")

    try:
        print(f"   - 브라우저로 URL 이동 중...")
        driver.get(url)  # URL 접속
        print(f"✅ [DEBUG] URL 접속 성공: {url}")

        # 자동차 이름 추출: 요소 탐색
        try:
            print(f"   - 페이지 요소 탐색 중...")
            name_element = driver.find_element(By.XPATH, '//h1[@class="car-name"]')  # 예시 XPath
            car_name = name_element.text if name_element else "데이터 없음"
            print(f"   - 추출된 차량 이름: {car_name}")
        except Exception as e:
            print(f"⚠️  [WARNING] 요소 탐색 실패: {str(e)}")
            car_name = "데이터 없음"

        result = {
            "url": url,
            "buyer": buyer,
            "car_name": car_name,
            "status": "COMPLETED" if car_name != "데이터 없음" else "FAILED"
        }

        if result["status"] == "FAILED":
            result["error"] = "페이지에서 데이터를 찾을 수 없습니다"

        print(f"✅ [DEBUG] process_url 결과: {result}")
        return result

    except Exception as e:
        error_msg = f"URL 처리 실패: {str(e)}"
        print(f"❌ [ERROR] {error_msg}")
        print(traceback.format_exc())
        return {
            "url": url,
            "buyer": buyer,
            "car_name": "데이터 없음",
            "status": "FAILED",
            "error": error_msg
        }

# =========================
# 메인 파이프라인 로직
# =========================
def run_pipeline(list_pairs, user_name, gcp_secrets, spreadsheet_name, headless=False):
    """
    실행 크롤링 로직.
    """
    logging.info(f"[run_pipeline] 시작")
    logging.info(f"   - list_pairs 개수: {len(list_pairs)}")
    logging.info(f"   - user_name: {user_name}")
    logging.info(f"   - spreadsheet_name: {spreadsheet_name}")
    logging.info(f"   - headless: {headless}")
    logging.info(f"   - gcp_secrets 타입: {type(gcp_secrets)}")
    
    print(f"\n🚀 [DEBUG] run_pipeline 시작")
    print(f"   - list_pairs 개수: {len(list_pairs)}")
    print(f"   - user_name: {user_name}")
    print(f"   - spreadsheet_name: {spreadsheet_name}")
    print(f"   - headless: {headless}")
    
    # Validate inputs
    if not list_pairs:
        logging.error("[run_pipeline] list_pairs가 비어있습니다")
        print(f"❌ [ERROR] list_pairs가 비어있습니다")
        return []
    
    if not gcp_secrets:
        logging.error("[run_pipeline] gcp_secrets가 비어있습니다")
        print(f"❌ [ERROR] gcp_secrets가 비어있습니다")
        return [{
            "url": url,
            "buyer": buyer,
            "status": "FAILED",
            "error": "GCP secrets가 제공되지 않음"
        } for url, buyer in list_pairs]
    
    if not spreadsheet_name:
        logging.error("[run_pipeline] spreadsheet_name이 비어있습니다")
        print(f"❌ [ERROR] spreadsheet_name이 비어있습니다")
        return [{
            "url": url,
            "buyer": buyer,
            "status": "FAILED",
            "error": "스프레드시트 이름이 제공되지 않음"
        } for url, buyer in list_pairs]
    
    # Connect to Google Sheets
    try:
        logging.info("[run_pipeline] Google Sheets 연결 시도 중...")
        print(f"   - Google Sheets 연결 시도 중...")
        spreadsheet = connect_to_google_sheet(gcp_secrets, spreadsheet_name)
        if not spreadsheet:
            logging.error("[run_pipeline] Google Sheets 연결 실패")
            print(f"❌ [ERROR] Google Sheets 연결 실패")
            # Return failed records for all pairs
            return [{
                "url": url,
                "buyer": buyer,
                "status": "FAILED",
                "error": "Google Sheets 연결 실패"
            } for url, buyer in list_pairs]
        logging.info("[run_pipeline] Google Sheets 연결 성공")
    except Exception as e:
        logging.error(f"[run_pipeline] Google Sheets 연결 오류: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"❌ [ERROR] Google Sheets 연결 오류: {str(e)}")
        print(traceback.format_exc())
        # Return failed records for all pairs
        return [{
            "url": url,
            "buyer": buyer,
            "status": "FAILED",
            "error": f"Google Sheets 연결 오류: {str(e)}"
        } for url, buyer in list_pairs]

    # Initialize driver
    driver = None
    try:
        logging.info("[run_pipeline] 크롬 드라이버 초기화 중...")
        print(f"   - 크롬 드라이버 초기화 중...")
        driver = make_driver(headless=headless)
        logging.info("[run_pipeline] 크롬 드라이버 초기화 성공")
        print(f"✅ [DEBUG] 크롬 드라이버 초기화 성공")
    except Exception as e:
        logging.error(f"[run_pipeline] 드라이버 초기화 실패: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"❌ [ERROR] 드라이버 초기화 실패: {str(e)}")
        print(traceback.format_exc())
        # Return failed records for all pairs
        return [{
            "url": url,
            "buyer": buyer,
            "status": "FAILED",
            "error": f"드라이버 초기화 실패: {str(e)}"
        } for url, buyer in list_pairs]
    
    completed_records = []
    try:
        for idx, (url, buyer) in enumerate(list_pairs):
            logging.info(f"[run_pipeline] 작업 {idx+1}/{len(list_pairs)} 처리")
            print(f"\n🌐 [DEBUG] 작업 {idx+1}/{len(list_pairs)} 처리")
            print(f"   - URL: {url}")
            print(f"   - Buyer: {buyer}")
            try:
                record = process_url(driver, url, buyer)
                if record:
                    completed_records.append(record)
                    logging.info(f"[run_pipeline] 레코드 추가 완료: {record}")
                    print(f"✅ [DEBUG] 레코드 추가 완료")
                else:
                    logging.warning("[run_pipeline] process_url이 None 반환")
                    print(f"⚠️  [WARNING] process_url이 None 반환")
                    completed_records.append({
                        "url": url,
                        "buyer": buyer,
                        "status": "FAILED",
                        "error": "process_url이 결과를 반환하지 않음"
                    })
            except Exception as e:
                error_msg = f"작업 실패: {str(e)}"
                logging.error(f"[run_pipeline] {error_msg}")
                logging.error(traceback.format_exc())
                print(f"❌ [ERROR] {error_msg}")
                print(traceback.format_exc())
                completed_records.append({
                    "url": url,
                    "buyer": buyer,
                    "status": "FAILED",
                    "error": error_msg
                })
    finally:
        if driver:
            try:
                logging.info("[run_pipeline] 드라이버 종료 중...")
                print(f"   - 드라이버 종료 중...")
                driver.quit()
                logging.info("[run_pipeline] 드라이버 종료 완료")
                print(f"✅ [DEBUG] 드라이버 종료 완료")
            except Exception as e:
                logging.warning(f"[run_pipeline] 드라이버 종료 실패: {str(e)}")
                print(f"⚠️  [WARNING] 드라이버 종료 실패: {str(e)}")

    logging.info(f"[run_pipeline] 완료 - 총 처리된 레코드: {len(completed_records)}")
    print(f"\n✅ [DEBUG] run_pipeline 완료")
    print(f"   - 총 처리된 레코드: {len(completed_records)}")
    print(f"   - completed_records: {completed_records}")
    return completed_records
