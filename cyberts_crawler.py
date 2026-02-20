from __future__ import annotations
import time
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- 설정값 ---
CYBERTS_URL = "https://www.cyberts.kr/ts/tis/ism/readTsTisInqireSvcMainView.do"
SPEC_INPUT_ID = "sFomConfmNo"
SEARCH_BUTTON_ID = "btnSearch"

FIELD_IDS = {
    "weight": "txtCarTotWt",  # 차량총중량
    "length": "txtObssLt",    # 길이
    "width": "txtLpirLt",      # 너비
    "height": "txtObssHg",    # 높이
}

def _build_chrome_options(headless: bool = True) -> Options:
    """리눅스/Streamlit Cloud 환경 최적화 옵션"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # 보안 및 자동화 탐지 우회
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Streamlit Cloud의 Chromium 실행 파일 경로 명시
    options.binary_location = "/usr/bin/chromium"
    
    return options

def _wait_nonempty_value_by_id(driver: webdriver.Chrome, element_id: str, timeout: int = 15) -> str:
    """요소가 존재하고 실제 값이 채워질 때까지 대기"""
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    # 값이 비어있지 않을 때까지 대기
    WebDriverWait(driver, timeout).until(
        lambda d: (el.get_attribute("value") or "").strip() != ""
    )
    return (el.get_attribute("value") or "").strip()

def fetch_vehicle_specs(
    spec_num: str,
    *,
    headless: bool = True
) -> Dict[str, Any]:
    """차량 제원 조회 메인 함수"""
    driver: Optional[webdriver.Chrome] = None

    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "message": "제원관리번호가 없습니다."}

        options = _build_chrome_options(headless=headless)
        
        # [핵심 수정] 시스템에 설치된 chromedriver 경로를 직접 지정
        # Streamlit Cloud 환경의 기본 경로입니다.
        service = Service("/usr/bin/chromedriver")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.get(CYBERTS_URL)

        # 1. 입력 필드 대기 및 입력
        spec_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, SPEC_INPUT_ID))
        )
        spec_input.clear()
        spec_input.send_keys(spec_num.strip())

        # 2. 조회 버튼 클릭
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, SEARCH_BUTTON_ID))
        )
        search_button.click()
        
        # 3. 데이터 렌더링을 위한 짧은 대기
        time.sleep(1.5)

        # 4. 결과값 수집
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                specs[key] = _wait_nonempty_value_by_id(driver, field_id)
            except TimeoutException:
                return {
                    "status": "error",
                    "message": f"항목({key})을 찾을 수 없거나 값이 비어있습니다. 번호를 확인하세요."
                }

        return {"status": "success", "data": specs}

    except WebDriverException as e:
        return {"status": "error", "message": f"브라우저 실행 오류: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"기타 오류: {str(e)}"}
    finally:
        if driver:
            driver.quit()
