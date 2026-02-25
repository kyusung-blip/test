from __future__ import annotations
import time
import re
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 에러 처리를 위해 UnexpectedAlertPresentException 추가
from selenium.common.exceptions import TimeoutException, WebDriverException, UnexpectedAlertPresentException, NoAlertPresentException

# --- 설정값 ---
CYBERTS_URL = "https://www.cyberts.kr/ts/tis/ism/readTsTisInqireSvcMainView.do"
SPEC_INPUT_ID = "sFomConfmNo"
SEARCH_BUTTON_ID = "btnSearch"

FIELD_IDS = {
    "weight": "txtCarTotWt",
    "length": "txtChssLt",
    "width": "txtChssBt",
    "height": "txtChssHg",
}

def _build_chrome_options(headless: bool = False) -> Options: # 기본값을 False로 변경
    options = Options()
    
    # 만약 Streamlit Cloud(리눅스 서버)에서 실행한다면 여전히 headless가 필요할 수 있습니다.
    # 하지만 로컬 PC 테스트라면 아래 headless 관련 줄을 주석 처리하세요.
    if headless:
        options.add_argument("--headless=new")

    # --- [핵심] 사람이 쓰는 브라우저처럼 위장하기 ---
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled") # 1. 자동화 제어 신호 끔
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) # 2. 자동화 표시줄 제거
    options.add_experimental_option("useAutomationExtension", False) # 3. 확장 프로그램 비활성화
    
    # 실제 사람이 쓰는듯한 User-Agent 설정
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    return options

def fetch_vehicle_specs(spec_num: str, *, headless: bool = False) -> Dict[str, Any]:
    driver: Optional[webdriver.Chrome] = None
    try:
        options = _build_chrome_options(headless=headless)
        driver = webdriver.Chrome(options=options)

        # 4. [매우 중요] navigator.webdriver 속성을 False로 강제 변경
        # 사이트 보안 시스템이 이 속성을 보고 봇인지 판단합니다.
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        driver.get(CYBERTS_URL)
        
        # 사람처럼 보이게 랜덤한 대기 시간 추가
        time.sleep(2) 

        # --- 번호 입력 단계 ---
        spec_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, SPEC_INPUT_ID))
        )
        
        # 한 글자씩 타이핑하는 효과 (사람처럼 보이게)
        spec_input.clear()
        for char in spec_num.strip():
            spec_input.send_keys(char)
            time.sleep(0.1) # 0.1초 간격으로 타이핑

        # 클릭 전 잠시 멈춤
        time.sleep(0.5)
        search_button = driver.find_element(By.ID, SEARCH_BUTTON_ID)
        search_button.click()

        # 2. 제원번호 입력 및 조회
        spec_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, SPEC_INPUT_ID))
        )
        spec_input.clear()
        spec_input.send_keys(spec_num.strip())

        search_button = driver.find_element(By.ID, SEARCH_BUTTON_ID)
        search_button.click()
        
        # 조회 후 데이터가 뜰 때까지 대기하면서 팝업 감시
        time.sleep(2.5)
        after_click_alert = check_alert()
        if after_click_alert:
            return {"status": "error", "message": f"조회 오류 팝업: {after_click_alert}"}

        # 3. 데이터 수집
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                # 짧은 대기 시간으로 요소 확인
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                raw_text = element.text.strip()
                
                if not raw_text:
                    specs[key] = "0"
                    continue
                
                clean_numbers = re.findall(r'\d+', raw_text)
                specs[key] = clean_numbers[0] if clean_numbers else "0"
                
            except TimeoutException:
                specs[key] = "0" # 못 찾으면 0으로 채우고 진행

        # 수집된 데이터가 모두 0이면 결과가 없는 것으로 간주
        if all(v == "0" for v in specs.values()):
             return {"status": "error", "message": "조회된 제원 데이터가 없습니다. 번호를 확인하세요."}

        return {"status": "success", "data": specs}

    except UnexpectedAlertPresentException:
        # 이 예외는 WebDriverWait 도중 발생하므로 다시 한번 팝업 체크
        try:
            alert = driver.switch_to.alert
            msg = alert.text
            alert.accept()
            return {"status": "error", "message": f"사이트 팝업: {msg}"}
        except:
            return {"status": "error", "message": "사이트 팝업이 감지되어 중단되었습니다."}

    except WebDriverException as e:
        return {"status": "error", "message": f"브라우저 실행 오류: {str(e)[:100]}"}
    finally:
        if driver:
            driver.quit()
