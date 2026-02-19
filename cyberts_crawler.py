"""
Cyberts 차량 제원 정보 크롤링 모듈 (디버그 덤프 포함)

정책:
- 차량 제원 4개 필드(총중량/길이/너비/높이) 중 하나라도
  (1) 요소가 없거나
  (2) value가 비어있으면
  => 실패(error)

디버그:
- 실패 시점에 스크린샷(.png) + 페이지소스(.html)를 저장해서
  실제로 어떤 화면을 보고 있었는지 확인할 수 있게 함.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional
import os
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


def _dump_debug(driver: webdriver.Chrome, prefix: str = "cyberts") -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.environ.get("CYBERTS_DEBUG_DIR", "/tmp")
    os.makedirs(out_dir, exist_ok=True)

    png_path = os.path.join(out_dir, f"{prefix}_{ts}.png")
    html_path = os.path.join(out_dir, f"{prefix}_{ts}.html")

    print("DEBUG dump dir:", os.path.abspath(out_dir))
    try:
        print("DEBUG cwd:", os.getcwd())
    except Exception:
        pass

    try:
        driver.save_screenshot(png_path)
        print("DEBUG screenshot saved:", png_path)
    except Exception as e:
        print("DEBUG screenshot save failed:", repr(e))

    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("DEBUG html saved:", html_path)
    except Exception as e:
        print("DEBUG html save failed:", repr(e))

    try:
        print("DEBUG url:", driver.current_url)
    except Exception as e:
        print("DEBUG url read failed:", repr(e))

    try:
        print("DEBUG title:", driver.title)
    except Exception as e:
        print("DEBUG title read failed:", repr(e))


def _build_chrome_options(headless: bool = True) -> Options:
    options = Options()
    if headless:
        # 환경에 따라 "--headless" 대신 "--headless=new"가 더 안정적일 수 있음
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options


def _wait_nonempty_value_by_id(driver: webdriver.Chrome, element_id: str, timeout: int = 20) -> str:
    """
    element_id가 나타나고, value가 비어있지 않을 때까지 기다린 뒤 value 반환.
    timeout 내에 value가 안 채워지면 TimeoutException 발생 (=> 실패 정책).
    """
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    WebDriverWait(driver, timeout).until(
        lambda d: (el.get_attribute("value") or "").strip() != ""
    )
    return (el.get_attribute("value") or "").strip()


def fetch_vehicle_specs(spec_num: str, *, headless: bool = True, debug_dump_on_fail: bool = True) -> Dict[str, Any]:
    """
    Cyberts 사이트에서 차량 제원 정보를 크롤링합니다.

    Args:
        spec_num: 제원관리번호
        headless: True면 브라우저 창 없이 실행, False면 실제 창 띄움(디버깅에 유리)
        debug_dump_on_fail: 실패 시 스크린샷/HTML 저장 여부

    Returns:
        {
            "status": "success"|"error",
            "data": {"weight":..., "length":..., "width":..., "height":...},
            "message": "..."
        }
    """
    driver: Optional[webdriver.Chrome] = None

    try:
        if not spec_num or not spec_num.strip():
            return {"status": "error", "data": {}, "message": "제원관리번호가 없습니다."}

        options = _build_chrome_options(headless=headless)
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
            if debug_dump_on_fail:
                _dump_debug(driver, prefix="cyberts_fail_no_spec_input")
            return {"status": "error", "data": {}, "message": "제원관리번호 입력 필드를 찾을 수 없습니다."}

        # 조회 버튼 클릭
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, SEARCH_BUTTON_ID))
            )
            search_button.click()
        except TimeoutException:
            if debug_dump_on_fail:
                _dump_debug(driver, prefix="cyberts_fail_no_search_button")
            return {"status": "error", "data": {}, "message": "조회 버튼을 찾을 수 없거나 클릭할 수 없습니다."}

        # 결과 필드 4개 모두: 존재 + value 채움까지 대기
        try:
            specs = {k: _wait_nonempty_value_by_id(driver, v, timeout=20) for k, v in FIELD_IDS.items()}
        except TimeoutException as e:
            if debug_dump_on_fail:
                _dump_debug(driver, prefix="cyberts_fail_timeout")
            return {
                "status": "error",
                "data": {},
                "message": f"조회 결과 필드 로딩/값 채움 대기 중 타임아웃: {str(e)}",
            }
        except NoSuchElementException as e:
            if debug_dump_on_fail:
                _dump_debug(driver, prefix="cyberts_fail_nosuchelement")
            return {
                "status": "error",
                "data": {},
                "message": f"차량 제원 필드를 찾을 수 없습니다: {str(e)}",
            }

        # 정책상: 값이 하나라도 비면 실패
        missing = [k for k, val in specs.items() if not val]
        if missing:
            if debug_dump_on_fail:
                _dump_debug(driver, prefix="cyberts_fail_empty_values")
            return {
                "status": "error",
                "data": {},
                "message": f"차량 제원 값이 비어있습니다: {', '.join(missing)}",
            }

        return {"status": "success", "data": specs, "message": "조회 성공"}

    except WebDriverException as e:
        # 크롬드라이버/브라우저 자체 문제
        if driver and debug_dump_on_fail:
            _dump_debug(driver, prefix="cyberts_fail_webdriver")
        return {"status": "error", "data": {}, "message": f"WebDriver 오류: {str(e)}"}

    except Exception as e:
        if driver and debug_dump_on_fail:
            _dump_debug(driver, prefix="cyberts_fail_unknown")
        return {"status": "error", "data": {}, "message": f"알 수 없는 오류: {str(e)}"}

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    sn = input("제원관리번호를 입력하세요: ").strip()

    # 1) 일단 headless=False로 테스트(진단에 유리)
    result = fetch_vehicle_specs(sn, headless=False, debug_dump_on_fail=True)

    print("\n결과:", result)
