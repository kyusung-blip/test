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

warnings.filterwarnings(action='ignore')

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
def connect_to_google_sheet(gcp_secrets, spreadsheet_name):
    """
    GCP 인증 정보를 이용해 Google Sheets에 연결.

    Args:
        gcp_secrets (dict): GCP Service Account 인증 정보
        spreadsheet_name (str): 열고자 하는 스프레드시트 이름
    Returns:
        gspread.Spreadsheet: 연결된 스프레드시트 객체
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secrets)
    gc = gspread.authorize(credentials)

    # Google 스프레드시트 열기
    try:
        spreadsheet = gc.open(spreadsheet_name)
        print(f"✅ {spreadsheet_name} 스프레드시트 열림")
        return spreadsheet
    except Exception as e:
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
        import traceback
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
    print(f"\n🚀 [DEBUG] run_pipeline 시작")
    print(f"   - list_pairs 개수: {len(list_pairs)}")
    print(f"   - user_name: {user_name}")
    print(f"   - spreadsheet_name: {spreadsheet_name}")
    print(f"   - headless: {headless}")
    
    # Validate inputs
    if not list_pairs:
        print(f"❌ [ERROR] list_pairs가 비어있습니다")
        return []
    
    # Connect to Google Sheets
    try:
        print(f"   - Google Sheets 연결 시도 중...")
        spreadsheet = connect_to_google_sheet(gcp_secrets, spreadsheet_name)
        if not spreadsheet:
            print(f"❌ [ERROR] Google Sheets 연결 실패")
            # Return failed records for all pairs
            return [{
                "url": url,
                "buyer": buyer,
                "status": "FAILED",
                "error": "Google Sheets 연결 실패"
            } for url, buyer in list_pairs]
    except Exception as e:
        print(f"❌ [ERROR] Google Sheets 연결 오류: {str(e)}")
        import traceback
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
        print(f"   - 크롬 드라이버 초기화 중...")
        driver = make_driver(headless=headless)
        print(f"✅ [DEBUG] 크롬 드라이버 초기화 성공")
    except Exception as e:
        print(f"❌ [ERROR] 드라이버 초기화 실패: {str(e)}")
        import traceback
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
            print(f"\n🌐 [DEBUG] 작업 {idx+1}/{len(list_pairs)} 처리")
            print(f"   - URL: {url}")
            print(f"   - Buyer: {buyer}")
            try:
                record = process_url(driver, url, buyer)
                if record:
                    completed_records.append(record)
                    print(f"✅ [DEBUG] 레코드 추가 완료")
                else:
                    print(f"⚠️  [WARNING] process_url이 None 반환")
                    completed_records.append({
                        "url": url,
                        "buyer": buyer,
                        "status": "FAILED",
                        "error": "process_url이 결과를 반환하지 않음"
                    })
            except Exception as e:
                error_msg = f"작업 실패: {str(e)}"
                print(f"❌ [ERROR] {error_msg}")
                import traceback
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
                print(f"   - 드라이버 종료 중...")
                driver.quit()
                print(f"✅ [DEBUG] 드라이버 종료 완료")
            except Exception as e:
                print(f"⚠️  [WARNING] 드라이버 종료 실패: {str(e)}")

    print(f"\n✅ [DEBUG] run_pipeline 완료")
    print(f"   - 총 처리된 레코드: {len(completed_records)}")
    print(f"   - completed_records: {completed_records}")
    return completed_records
