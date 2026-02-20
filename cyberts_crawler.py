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
    return options

def fetch_vehicle_specs(spec_num: str, *, headless: bool = True) -> Dict[str, Any]:
    """차량 제원 조회 (수정 버전)"""
    driver: Optional[webdriver.Chrome] = None
    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "message": "제원관리번호가 없습니다."}

        # 1. 옵션 설정
        options = _build_chrome_options(headless=headless)
        
        # 2. 브라우저 실행 (service 인자를 제거했습니다)
        # 시스템에 설치된 chromedriver를 자동으로 찾습니다.
        driver = webdriver.Chrome(options=options) 
        
        driver.get(CYBERTS_URL)

        # 3. 제원번호 입력 및 조회 버튼 클릭
        spec_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, SPEC_INPUT_ID))
        )
        spec_input.clear()
        spec_input.send_keys(spec_num.strip())

        search_button = driver.find_element(By.ID, SEARCH_BUTTON_ID)
        search_button.click()
        
        # 4. 결과 테이블 로딩 대기
        time.sleep(2.5)

        # 5. 데이터 수집
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                raw_text = element.text.strip()
                
                if not raw_text:
                    # 값이 비어있어도 진행하도록 수정 (에러로 중단되지 않게)
                    specs[key] = ""
                    continue
                
                # 숫자만 추출
                clean_numbers = re.findall(r'\d+', raw_text)
                specs[key] = clean_numbers[0] if clean_numbers else raw_text
                
            except TimeoutException:
                # 항목 하나를 못 찾아도 전체가 죽지 않도록 에러 메시지 반환
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
