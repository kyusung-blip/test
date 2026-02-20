from __future__ import annotations
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# 상수 정의
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
    """리눅스 서버 및 Streamlit Cloud 환경에 최적화된 크롬 옵션 설정"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # 자동화 탐지 우회 (일부 공공기관 사이트 차단 방지)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # (선택 사항) Streamlit Cloud에서 특정 경로가 필요할 경우
    # options.binary_location = "/usr/bin/google-chrome"
    
    return options

def _wait_nonempty_value_by_id(driver: webdriver.Chrome, element_id: str, timeout: int = 20) -> str:
    """요소가 존재하고 value가 채워질 때까지 대기"""
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    # 데이터 로딩 시간 고려: value가 빌 경우를 대비해 반복 확인
    WebDriverWait(driver, timeout).until(
        lambda d: (el.get_attribute("value") or "").strip() != ""
    )
    return (el.get_attribute("value") or "").strip()

def fetch_vehicle_specs(
    spec_num: str,
    *,
    headless: bool = True,
    require_nonempty_values: bool = True,
) -> Dict[str, Any]:
    """차량 제원 조회 메인 함수"""
    driver: Optional[webdriver.Chrome] = None

    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "data": {}, "message": "제원관리번호가 입력되지 않았습니다."}

        options = _build_chrome_options(headless=headless)
        
        # WebDriverManager를 통한 드라이버 자동 설치 및 서비스 생성
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 탐지 우회: navigator.webdriver 속성 제거
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        driver.set_page_load_timeout(30)
        driver.get(CYBERTS_URL)

        # 1. 제원관리번호 입력
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
        
        # 3. 데이터 로딩 대기 (서버 응답 속도에 맞춰 잠시 대기)
        time.sleep(1)

        # 4. 결과 필드 추출
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                if require_nonempty_values:
                    specs[key] = _wait_nonempty_value_by_id(driver, field_id, timeout=15)
                else:
                    el = driver.find_element(By.ID, field_id)
                    specs[key] = (el.get_attribute("value") or "").strip()
            except TimeoutException:
                return {
                    "status": "error",
                    "data": {},
                    "message": f"제원 항목({key}) 로딩 실패. 제원번호가 정확한지 확인하세요."
                }

        return {"status": "success", "data": specs, "message": "조회 성공"}

    except WebDriverException as e:
        return {"status": "error", "data": {}, "message": f"브라우저 실행 오류: {str(e)}"}
    except Exception as e:
        return {"status": "error", "data": {}, "message": f"기타 오류: {str(e)}"}
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # 터미널 테스트용
    sn = input("제원관리번호 입력: ").strip()
    res = fetch_vehicle_specs(sn, headless=False)
    print("\n[결과]", res)
