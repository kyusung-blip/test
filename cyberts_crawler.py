"""
Cyberts 차량 제원 정보 크롤링 모듈

정책:
- 결과 필드(총중량/길이/너비/높이) 중 하나라도
  (1) 요소가 안 나타나거나
  (2) value가 끝내 채워지지 않으면
  => 실패(error) 처리
"""

from __future__ import annotations

from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


CYBERTS_URL = "https://www.cyberts.kr/ts/tis/ism/readTsTisInqireSvcMainView.do"

SPEC_INPUT_ID = "sFomConfmNo"
SEARCH_BUTTON_ID = "btnSearch"

FIELD_IDS = {
    "weight": "txtCarTotWt",  # 차량총중량
    "length": "txtObssLt",    # 길이
    "width": "txtLpirLt",     # 너비
    "height": "txtObssHg",    # 높이
}


def _build_chrome_options() -> Options:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options


def _wait_nonempty_value_by_id(driver: webdriver.Chrome, element_id: str, timeout: int) -> str:
    """
    element_id가 나타나고, value가 비어있지 않게 될 때까지 기다린 뒤 value를 반환.
    - timeout 내에 value가 채워지지 않으면 TimeoutException 발생 (=> 실패 정책에 부합)
    """
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )

    WebDriverWait(driver, timeout).until(
        lambda d: (el.get_attribute("value") or "").strip() != ""
    )

    return (el.get_attribute("value") or "").strip()


def fetch_vehicle_specs(spec_num: str) -> Dict[str, Any]:
    driver: Optional[webdriver.Chrome] = None

    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "data": {}, "message": "제원관리번호가 없습니다."}

        options = _build_chrome_options()
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        driver.get(CYBERTS_URL)

        # 제원관리번호 입력
        try:
            spec_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, SPEC_INPUT_ID))
            )
            spec_input.clear()
            spec_input.send_keys(spec_num.strip())
        except TimeoutException:
            return {"status": "error", "data": {}, "message": "제원관리번호 입력 필드를 찾을 수 없습니다."}

        # 조회 버튼 클릭
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, SEARCH_BUTTON_ID))
            )
            search_button.click()
        except TimeoutException:
            return {"status": "error", "data": {}, "message": "조회 버튼을 찾을 수 없거나 클릭할 수 없습니다."}

        # 결과 필드 4개 모두 "존재 + value 채움"까지 대기 (하나라도 안되면 실패)
        try:
            specs = {
                key: _wait_nonempty_value_by_id(driver, field_id, timeout=20)
                for key, field_id in FIELD_IDS.items()
            }
        except TimeoutException as e:
            return {
                "status": "error",
                "data": {},
                "message": f"조회 결과 필드 로딩/값 채움 대기 중 타임아웃: {str(e)}",
            }
        except NoSuchElementException as e:
            return {"status": "error", "data": {}, "message": f"차량 제원 필드를 찾을 수 없습니다: {str(e)}"}

        # 방어적 검증(이론상 여기 걸리진 않지만, 정책 명확화용)
        missing = [k for k, v in specs.items() if not v]
        if missing:
            return {
                "status": "error",
                "data": {},
                "message": f"차량 제원 값이 비어있습니다: {', '.join(missing)}",
            }

        return {"status": "success", "data": specs, "message": "조회 성공"}

    except WebDriverException as e:
        return {"status": "error", "data": {}, "message": f"WebDriver 오류: {str(e)}"}
    except Exception as e:
        return {"status": "error", "data": {}, "message": f"알 수 없는 오류: {str(e)}"}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    test_spec_num = input("제원관리번호를 입력하세요: ").strip()
    print(fetch_vehicle_specs(test_spec_num))
