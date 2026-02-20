from __future__ import annotations
import time
import re
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

# 알려주신 정확한 ID 반영 (td 태그)
FIELD_IDS = {
    "weight": "txtCarTotWt",  # 차량총중량
    "length": "txtChssLt",    # 길이 (알려주신 ID)
    "width": "txtChssBt",     # 너비 (알려주신 ID)
    "height": "txtChssHg",    # 높이 (알려주신 ID)
}

def _build_chrome_options(headless: bool = True) -> Options:
    """리눅스/Streamlit Cloud 최적화 옵션"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Streamlit Cloud Chromium 경로
    options.binary_location = "/usr/bin/chromium"
    return options

def fetch_vehicle_specs(spec_num: str, *, headless: bool = True) -> Dict[str, Any]:
    """차량 제원 조회 (td 텍스트 추출 방식)"""
    driver: Optional[webdriver.Chrome] = None
    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "message": "제원관리번호가 없습니다."}

        options = _build_chrome_options(headless=headless)
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(CYBERTS_URL)

        # 1. 제원번호 입력 및 조회 버튼 클릭
        spec_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, SPEC_INPUT_ID))
        )
        spec_input.clear()
        spec_input.send_keys(spec_num.strip())

        search_button = driver.find_element(By.ID, SEARCH_BUTTON_ID)
        search_button.click()
        
        # 2. 결과 테이블 로딩 대기
        time.sleep(2.5)

        # 3. 각 필드 데이터 수집 (td 태그의 텍스트 읽기)
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                # td 요소가 나타날 때까지 대기
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                
                # <td> 태그는 .text로 값을 가져와야 함 (예: "2370(0)" 또는 "4700")
                raw_text = element.text.strip()
                
                if not raw_text:
                    return {"status": "error", "message": f"항목({key})의 값이 비어있습니다."}
                
                # 정규식으로 숫자만 추출 (예: "2370(0)" -> "2370")
                # 단위(kg, mm 등)나 불필요한 괄호를 제거합니다.
                clean_numbers = re.findall(r'\d+', raw_text)
                specs[key] = clean_numbers[0] if clean_numbers else raw_text
                
            except TimeoutException:
                return {
                    "status": "error", 
                    "message": f"항목({key})을 찾을 수 없습니다. (ID: {field_id})"
                }

        return {"status": "success", "data": specs}

    except WebDriverException as e:
        return {"status": "error", "message": f"브라우저 실행 오류: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"시스템 오류: {str(e)}"}
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # 테스트 실행
    test_num = "입력 테스트 번호"
    print(fetch_vehicle_specs(test_num, headless=False))
