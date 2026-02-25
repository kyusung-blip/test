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

def _build_chrome_options(headless: bool = True) -> Options:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # 자동화 탐지 방지를 위한 유저 에이전트 추가 (차단 방지)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return options

def fetch_vehicle_specs(spec_num: str, *, headless: bool = True) -> Dict[str, Any]:
    driver: Optional[webdriver.Chrome] = None
    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "message": "제원관리번호가 없습니다."}

        options = _build_chrome_options(headless=headless)
        driver = webdriver.Chrome(options=options) 
        
        driver.get(CYBERTS_URL)

        # 1. 제원번호 입력 및 조회
        # 입력 전 Alert이 있는지 먼저 체크 (사이트 초기 진입 시 오류 방지)
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            return {"status": "error", "message": f"접속 초기 팝업 발생: {alert_text}"}
        except NoAlertPresentException:
            pass

        spec_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, SPEC_INPUT_ID))
        )
        spec_input.clear()
        spec_input.send_keys(spec_num.strip())

        search_button = driver.find_element(By.ID, SEARCH_BUTTON_ID)
        search_button.click()
        
        # 2. 결과 테이블 로딩 대기
        # 이 시점에서 "시스템 오류" Alert이 뜰 가능성이 큼
        time.sleep(2.0)

        # 3. 데이터 수집
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                # 각 항목을 찾기 전 Alert 체크
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                raw_text = element.text.strip()
                
                if not raw_text:
                    specs[key] = "0"
                    continue
                
                clean_numbers = re.findall(r'\d+', raw_text)
                specs[key] = clean_numbers[0] if clean_numbers else raw_text
                
            except TimeoutException:
                # 특정 항목을 못 찾을 때 Alert이 떠 있는지 확인
                try:
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    alert.accept()
                    return {"status": "error", "message": f"조회 중 사이트 팝업 발생: {alert_text}"}
                except NoAlertPresentException:
                    specs[key] = "0"

        return {"status": "success", "data": specs}

    except UnexpectedAlertPresentException as e:
        # 예상치 못한 Alert이 발생했을 때 텍스트 추출 후 닫기
        alert_text = "알 수 없는 오류"
        try:
            alert_text = driver.switch_to.alert.text
            driver.switch_to.alert.accept()
        except:
            pass
        return {"status": "error", "message": f"사이트 팝업 오류: {alert_text}"}

    except WebDriverException as e:
        return {"status": "error", "message": f"브라우저 실행 오류: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"시스템 오류: {str(e)}"}
    finally:
        if driver:
            driver.quit()
