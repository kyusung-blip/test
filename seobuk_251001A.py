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
    print(f"🚀 [DEBUG] 크롤링 시작 - URL: {url}, Buyer: {buyer}")

    try:
        driver.get(url)  # URL 접속
        print(f"✅ [DEBUG] URL 접속 성공: {url}")

        # 자동차 이름 추출: 요소 탐색
        try:
            name_element = driver.find_element(By.XPATH, '//h1[@class="car-name"]')  # 예시 XPath
            car_name = name_element.text if name_element else "데이터 없음"
        except Exception as e:
            print(f"❌ [ERROR] 요소 탐색 실패: {e}")
            car_name = "데이터 없음"

        result = {
            "url": url,
            "buyer": buyer,
            "car_name": car_name,
            "status": "COMPLETED" if car_name != "데이터 없음" else "FAILED"
        }

        print(f"✅ [DEBUG] 작업 결과: {result}")
        return result

    except Exception as e:
        print(f"❌ [ERROR] 전체 작업 실패: {e}")
        return {"url": url, "buyer": buyer, "status": "FAILED", "error": str(e)}

# =========================
# 메인 파이프라인 로직
# =========================
def run_pipeline(list_pairs, user_name, gcp_secrets, spreadsheet_name, headless=False):
    """
    실행 크롤링 로직.
    """
    print("🚀 [DEBUG] run_pipeline 시작")
    try:
        spreadsheet = connect_to_google_sheet(gcp_secrets, spreadsheet_name)
        if not spreadsheet:
            print(f"❌ [ERROR] Google Sheets 연결 실패.")
            return []
    except Exception as e:
        print(f"❌ [ERROR] Google Sheets 연결 오류: {e}")
        return []

    driver = make_driver(headless=headless)
    completed_records = []
    for idx, (url, buyer) in enumerate(list_pairs):
        print(f"🌐 [DEBUG] 현재 작업 - URL: {url}, Buyer: {buyer}")
        try:
            record = process_url(driver, url, buyer)
            completed_records.append(record)
        except Exception as e:
            print(f"❌ [ERROR] 작업 실패: {e}")

    driver.quit()
    print(f"✅ [DEBUG] 작업 완료 기록: {completed_records}")
    return completed_records
