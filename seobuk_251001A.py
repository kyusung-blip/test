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
    단일 URL과 Buyer를 처리. 결과 데이터를 생성.
    """
    print(f"🚀 DEBUG: process_url 시작 - URL: {url}, Buyer: {buyer}")
    try:
        # 예제 로직: URL과 Buyer 데이터를 기반으로 처리 수행
        record = {
            "url": url,
            "buyer": buyer,
            "status": "COMPLETED"  # 상태를 단순히 "COMPLETED"로 설정 (예제)
        }
        print(f"✅ process_url 결과: {record}")
        return record
    except Exception as e:
        print(f"❌ ERROR in process_url - {e}")
        return {"url": url, "buyer": buyer, "status": "FAILED"}

# =========================
# 메인 파이프라인 로직
# =========================
def run_pipeline(list_pairs, user_name, gcp_secrets, spreadsheet_name, headless=False):
    """
    `execute_crawling`으로 전달받은 데이터를 사용하여 크롤링 수행.
    """
    print("🚀 DEBUG: run_pipeline 함수 시작")
    print(f"✅ list_pairs: {list_pairs} (URL과 Buyer 정보 목록)")
    print(f"✅ user_name: {user_name} (Sales 팀 이름)")
    print(f"✅ gcp_secrets 전달됨? {bool(gcp_secrets)}")
    print(f"✅ spreadsheet_name: {spreadsheet_name}")

    # Google Sheets 연결 확인
    try:
        spreadsheet = connect_to_google_sheet(gcp_secrets, spreadsheet_name)
        if not spreadsheet:
            print(f"❌ ERROR: Google Sheet에 연결 실패 - {spreadsheet_name}")
            return []
    except Exception as e:
        print(f"❌ ERROR: Google Sheets 연결 중 오류 - {e}")
        return []

    # WebDriver 초기화
    driver = make_driver(headless=headless)
    print(f"✅ WebDriver 생성 완료 - Headless 모드: {headless}")

    # 크롤링 작업 수행
    completed_records = []
    for idx, (url, buyer) in enumerate(list_pairs):
        print(f"🌐 DEBUG: 크롤링 중 - {idx+1}/{len(list_pairs)}, URL: {url}, Buyer: {buyer}")
        try:
            record = process_url(driver, url, buyer)
            print(f"✅ 크롤링 성공 - 결과: {record}")
            completed_records.append(record)
        except Exception as e:
            print(f"❌ ERROR: 크롤링 실패 (URL: {url}) - {e}")

    driver.quit()
    print("🚀 DEBUG: run_pipeline 완료")
    return completed_records
