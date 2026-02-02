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
    print(f"Processing URL: {url} for Buyer: {buyer}")
    # 예제 로직: URL과 Buyer 데이터를 simple dictionary로 반환
    return {
        "url": url,
        "buyer": buyer,
        "status": "COMPLETED"
    }

# =========================
# 메인 파이프라인 로직
# =========================
def run_pipeline(list_pairs, user_name, gcp_secrets, spreadsheet_name, headless=False):
    """
    GCP 인증 정보와 지정된 스프레드시트로 크롤링 실행.

    Args:
        list_pairs (list): URL 및 Buyer 정보
        user_name (str): 실행 사용자
        gcp_secrets (dict): Google 서비스 계정 인증 정보
        spreadsheet_name (str): 작업 대상 Google 스프레드시트 이름
        headless (bool): Headless 모드 여부
    Returns:
        list: 크롤링 작업 결과 리스트
    """
    print("🔧 DEBUG: run_pipeline 시작...")
    print(f"✅ PARAMETERS: list_pairs={list_pairs}, user_name={user_name}, spreadsheet_name={spreadsheet_name}")
    
    # Google Sheets 연결 확인
    try:
        spreadsheet = connect_to_google_sheet(gcp_secrets, spreadsheet_name)
        if not spreadsheet:
            print(f"❌ WARNING: Google Sheet 연결 실패 - {spreadsheet_name}")
            return []
    except Exception as e:
        print(f"❌ ERROR: Google Sheets 연결 중 오류 발생 - {str(e)}")
        return []

    # WebDriver 초기화
    driver = make_driver(headless=headless)
    print(f"✅ WebDriver 생성 완료 - Headless: {headless}")
    
    completed_records = []
    for idx, (url, buyer) in enumerate(list_pairs):
        print(f"🔧 DEBUG: [{idx + 1}/{len(list_pairs)}] URL: {url}, Buyer: {buyer}")
        try:
            record = process_url(driver, url, buyer)  # 개별 URL 처리
            print(f"✅ 크롤링 성공: {record}")
            completed_records.append(record)
        except Exception as e:
            print(f"❌ ERROR: 크롤링 실패 - URL: {url}, ERROR: {str(e)}")
    driver.quit()
    print("🔧 DEBUG: run_pipeline 완료")
    return completed_records
