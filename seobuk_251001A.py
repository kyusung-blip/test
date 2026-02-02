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
    전체 크롤링 파이프라인 실행.

    Args:
        list_pairs (list): URL 및 Buyer 정보가 포함된 리스트
        user_name (str): 실행 중인 사용자 정보
        gcp_secrets (dict): GCP 인증 정보
        spreadsheet_name (str): 사용할 Google 스프레드시트의 이름
        headless (bool): Chrome을 headless 모드로 사용할지 여부
    Returns:
        list: 크롤링 결과 리스트
    """
    # Google Sheets 연결 설정
    spreadsheet = connect_to_google_sheet(gcp_secrets, spreadsheet_name)
    if not spreadsheet:
        return []

    # WebDriver 생성
    driver = make_driver(headless=headless)

    # 크롤링 작업 실행
    completed_records = []
    for idx, (url, buyer) in enumerate(list_pairs):
        print(f"🚀 [{idx+1}/{len(list_pairs)}] - URL: {url}, Buyer: {buyer}")
        record = process_url(driver, url, buyer)
        completed_records.append(record)

    # WebDriver 종료
    driver.quit()
    return completed_records
