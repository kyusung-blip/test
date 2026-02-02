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

    Args:
        driver (webdriver.Chrome): Selenium WebDriver 객체
        url (str): 크롤링 대상 URL
        buyer (str): Buyer 이름
    Returns:
        dict: 크롤링 작업 결과
    """
    print(f"🚀 [DEBUG] 크롤링 시작 - URL: {url}, Buyer: {buyer}")

    try:
        driver.get(url)  # URL 접속
        print(f"✅ [DEBUG] URL 접속 성공 - {url}")

        # 특정 타겟 요소 추출 (예: 자동차 이름 가져오기)
        # 반드시 잘못된 경우를 대비해 확인 로직 추가
        try:
            name_element = driver.find_element(By.XPATH, '//h1[@class="car-name"]')  # 예시 XPath
            car_name = name_element.text if name_element else "UNKNOWN"
        except Exception as e:
            print(f"❌ [ERROR] 데이터 탐색 실패 - {e}")
            car_name = "UNKNOWN"

        result = {
            "url": url,
            "buyer": buyer,
            "car_name": car_name,
            "status": "COMPLETED" if car_name != "UNKNOWN" else "FAILED"
        }

        if car_name == "UNKNOWN":
            print(f"❌ [DEBUG] 작업 실패 - 데이터가 비어 있음: {result}")
        else:
            print(f"✅ [DEBUG] 크롤링 성공: {result}")

        return result

    except Exception as e:
        # URL 접속 실패를 비롯한 모든 예외 처리
        print(f"❌ [ERROR] 크롤링 작업 전체 실패 - URL: {url}, Error: {e}")
        return {"url": url, "buyer": buyer, "status": "FAILED", "error": str(e)}

# =========================
# 메인 파이프라인 로직
# =========================
def run_pipeline(list_pairs, user_name, gcp_secrets, spreadsheet_name, headless=False):
    """
    GCP 인증 정보와 지정된 스프레드시트로 크롤링 실행.

    Args:
        list_pairs (list): URL 및 Buyer 정보가 포함된 리스트
        user_name (str): 실행 중인 사용자 정보
        gcp_secrets (dict): GCP Service Account 인증 정보
        spreadsheet_name (str): 사용할 Google 스프레드시트의 이름
        headless (bool): Chrome을 headless 모드로 사용할지 여부
    Returns:
        list: 크롤링 작업 결과 리스트
    """
    print("🚀 [DEBUG] run_pipeline 함수 시작")
    print(f"✅ list_pairs: {list_pairs}, user_name: {user_name}, spreadsheet_name: {spreadsheet_name}")

    # Google Sheets 연결 설정
    spreadsheet = connect_to_google_sheet(gcp_secrets, spreadsheet_name)
    if not spreadsheet:
        print(f"❌ [ERROR] Google Sheets 연결 실패: {spreadsheet_name}")
        return []

    # WebDriver 생성
    driver = make_driver(headless=headless)
    print(f"✅ [DEBUG] WebDriver 생성 완료 - Headless 여부: {headless}")
    
    completed_records = []
    for idx, (url, buyer) in enumerate(list_pairs):
        print(f"🚀 [DEBUG] [{idx+1}/{len(list_pairs)}] 크롤링 중 - URL: {url}, Buyer: {buyer}")
        record = process_url(driver, url, buyer)
        completed_records.append(record)

    driver.quit()
    print(f"🚀 [DEBUG] run_pipeline 종료 - 완료된 기록: {completed_records}")
    return completed_records
