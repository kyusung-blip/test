from __future__ import annotations
import time
import re
import os
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException, 
    UnexpectedAlertPresentException, 
    NoAlertPresentException
)

CYBERTS_URL = "https://www.cyberts.kr/ts/tis/ism/readTsTisInqireSvcMainView.do"
SPEC_INPUT_ID = "sFomConfmNo"
SEARCH_BUTTON_ID = "btnSearch"

FIELD_IDS = {
    "weight": "txtCarTotWt",
    "length": "txtChssLt",
    "width": "txtChssBt",
    "height": "txtChssHg",
}

def _build_chrome_options(headless: bool = True) -> Options:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # --- 보안 우회 설정 ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    return options

def fetch_vehicle_specs(spec_num: str, *, headless: bool = True) -> Dict[str, Any]:
    driver: Optional[webdriver.Chrome] = None
    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "message": "제원관리번호가 없습니다."}

        options = _build_chrome_options(headless=headless)
        driver = webdriver.Chrome(options=options)
        
        # 웹드라이버 속성 변조 (보안 우회 핵심)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

        driver.get(CYBERTS_URL)
        time.sleep(1.5)

        # 팝업 체크 함수
        def get_alert_text():
            try:
                alert = driver.switch_to.alert
                text = alert.text
                alert.accept()
                return text
            except NoAlertPresentException:
                return None

        # 1. 제원번호 입력 및 검색
        spec_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, SPEC_INPUT_ID)))
        spec_input.clear()
        # 사람처럼 한글자씩 입력
        for char in spec_num.strip():
            spec_input.send_keys(char)
            time.sleep(0.05)
        
        driver.find_element(By.ID, SEARCH_BUTTON_ID).click()
        
        # 2. 결과 대기 및 팝업 확인
        time.sleep(2.5)
        alert_msg = get_alert_text()
        if alert_msg:
            return {"status": "error", "message": f"조회 오류 팝업: {alert_msg}"}

        # 3. 데이터 수집
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, field_id)))
                raw_text = element.text.strip()
                clean_numbers = re.findall(r'\d+', raw_text)
                specs[key] = clean_numbers[0] if clean_numbers else "0"
            except:
                specs[key] = "0"

        if all(v == "0" for v in specs.values()):
            return {"status": "error", "message": "데이터를 찾을 수 없습니다."}

        return {"status": "success", "data": specs}

    except UnexpectedAlertPresentException:
        try:
            alert = driver.switch_to.alert
            msg = alert.text
            alert.accept()
            return {"status": "error", "message": f"사이트 팝업: {msg}"}
        except:
            return {"status": "error", "message": "사이트 오류 발생"}
    except Exception as e:
        return {"status": "error", "message": f"브라우저 오류: {str(e)[:50]}"}
    finally:
        if driver:
            driver.quit()
