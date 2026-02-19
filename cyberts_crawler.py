"""
Cyberts 차량 제원 정보 크롤링 모듈 (Streamlit/Cloud 디버깅 강화 + iframe/문자열 체크 포함)

정책:
- 차량 제원 4개 필드(총중량/길이/너비/높이) 중 하나라도
  (1) 요소가 없거나
  (2) value가 비어있으면
  => 실패(error)

디버그:
- 실패 시점에 스크린샷(.png) + 페이지소스(.html)를 /tmp(또는 CYBERTS_DEBUG_DIR)에 저장 시도
- Streamlit Cloud에서 파일을 직접 확인하기 어려우므로 Logs에 다음을 함께 출력:
  - url/title
  - iframe 개수 및 일부 iframe 속성
  - page_source에 특정 id 문자열 포함 여부(txtCarTotWt, txtObssLt)

중요:
- 디버그 덤프가 실패하더라도 앱이 죽지 않도록 _safe_dump_debug로 보호
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
    """
    실패 시점의 증거 확보용:
    - 스크린샷: /tmp/{prefix}_{timestamp}.png (또는 CYBERTS_DEBUG_DIR)
    - HTML     : /tmp/{prefix}_{timestamp}.html
    - Logs 출력: url/title/cwd/out_dir + iframe 정보 + page_source 문자열 포함 여부
    """
    import os as _os  # Streamlit reload/namespace 꼬임 방지용 로컬 import

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = _os.environ.get("CYBERTS_DEBUG_DIR", "/tmp")
    _os.makedirs(out_dir, exist_ok=True)

    png_path = _os.path.join(out_dir, f"{prefix}_{ts}.png")
    html_path = _os.path.join(out_dir, f"{prefix}_{ts}.html")

    print("DEBUG dump dir:", _os.path.abspath(out_dir))
    try:
        print("DEBUG cwd:", _os.getcwd())
    except Exception as e:
        print("DEBUG cwd read failed:", repr(e))

    # URL / Title
    try:
        print("DEBUG url:", driver.current_url)
    except Exception as e:
        print("DEBUG url read failed:", repr(e))

    try:
        print("DEBUG title:", driver.title)
    except Exception as e:
        print("DEBUG title read failed:", repr(e))

    # iframe 여부 확인
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print("DEBUG iframe count:", len(iframes))
        for i, fr in enumerate(iframes[:5]):
            print(
                f"DEBUG iframe[{i}] id={fr.get_attribute('id')} "
                f"name={fr.get_attribute('name')} src={fr.get_attribute('src')}"
            )
    except Exception as e:
        print("DEBUG iframe inspect failed:", repr(e))

    # page_source에 특정 문자열이 포함되는지 (DOM 자체가 기대와 다른지 빠르게 판단)
    try:
        ps = driver.page_source or ""
        print("DEBUG contains txtCarTotWt:", "txtCarTotWt" in ps)
        print("DEBUG contains txtObssLt:", "txtObssLt" in ps)
    except Exception as e:
        print("DEBUG page_source check failed:", repr(e))

    # 파일 저장
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


def _safe_dump_debug(driver: Optional[webdriver.Chrome], prefix: str) -> None:
    """덤프가 실패해도 앱이 죽지 않도록 보호."""
    if not driver:
        return
    try:
        _dump_debug(driver, prefix=prefix)
    except Exception as dump_err:
        print("DEBUG dump failed:", repr(dump_err))


def _build_chrome_options(headless: bool = True) -> Options:
    options = Options()
    if headless:
        # 환경에 따라 "--headless" 대신 "--headless=new"가 더 안정적일 수 있음
        options.add_argument("--headless")
        # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options


def _wait_value_by_id(driver: webdriver.Chrome, element_id: str, timeout: int = 20) -> str:
    """요소 존재를 기다린 뒤 value를 읽음(value가 비어있을 수 있음)."""
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    return (el.get_attribute("value") or "").strip()


def _wait_nonempty_value_by_id(driver: webdriver.Chrome, element_id: str, timeout: int = 20) -> str:
    """
    요소 존재 + value가 비어있지 않게 될 때까지 기다린 뒤 value 반환.
    timeout 내에 value가 안 채워지면 TimeoutException 발생 (=> 실패 정책).
    """
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    WebDriverWait(driver, timeout).until(
        lambda d: (el.get_attribute("value") or "").strip() != ""
    )
    return (el.get_attribute("value") or "").strip()


def fetch_vehicle_specs(
    spec_num: str,
    *,
    headless: bool = True,
    debug_dump_on_fail: bool = True,
    require_nonempty_values: bool = True,
) -> Dict[str, Any]:
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
        except TimeoutException as e:
            if debug_dump_on_fail:
                _safe_dump_debug(driver, prefix="cyberts_fail_no_spec_input")
            return {"status": "error", "data": {}, "message": f"제원관리번호 입력 필드 타임아웃: {repr(e)}"}

        # 조회 버튼 클릭
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, SEARCH_BUTTON_ID))
            )
            search_button.click()
        except TimeoutException as e:
            if debug_dump_on_fail:
                _safe_dump_debug(driver, prefix="cyberts_fail_no_search_button")
            return {"status": "error", "data": {}, "message": f"조회 버튼 클릭 타임아웃: {repr(e)}"}

        # 결과 필드 4개 읽기 (필드별로 어디서 막히는지 메시지에 남김)
        specs: Dict[str, str] = {}
        for key, field_id in FIELD_IDS.items():
            try:
                if require_nonempty_values:
                    specs[key] = _wait_nonempty_value_by_id(driver, field_id, timeout=20)
                else:
                    specs[key] = _wait_value_by_id(driver, field_id, timeout=20)
            except TimeoutException as e:
                if debug_dump_on_fail:
                    _safe_dump_debug(driver, prefix=f"cyberts_fail_timeout_{key}_{field_id}")
                return {
                    "status": "error",
                    "data": {},
                    "message": f"필드 로딩/값 채움 타임아웃: {key} ({field_id}) / {repr(e)}",
                }
            except NoSuchElementException as e:
                if debug_dump_on_fail:
                    _safe_dump_debug(driver, prefix=f"cyberts_fail_nosuchelement_{key}_{field_id}")
                return {
                    "status": "error",
                    "data": {},
                    "message": f"차량 제원 필드를 찾을 수 없습니다: {key} ({field_id}) / {repr(e)}",
                }

        # 정책상: 값이 하나라도 비면 실패
        missing = [k for k, val in specs.items() if not val]
        if missing:
            if debug_dump_on_fail:
                _safe_dump_debug(driver, prefix="cyberts_fail_empty_values")
            return {
                "status": "error",
                "data": specs,
                "message": f"차량 제원 값이 비어있습니다: {', '.join(missing)}",
            }

        return {"status": "success", "data": specs, "message": "조회 성공"}

    except WebDriverException as e:
        if debug_dump_on_fail:
            _safe_dump_debug(driver, prefix="cyberts_fail_webdriver")
        return {"status": "error", "data": {}, "message": f"WebDriver 오류: {repr(e)}"}

    except Exception as e:
        if debug_dump_on_fail:
            _safe_dump_debug(driver, prefix="cyberts_fail_unknown")
        return {"status": "error", "data": {}, "message": f"알 수 없는 오류: {repr(e)}"}

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    sn = input("제원관리번호를 입력하세요: ").strip()
    result = fetch_vehicle_specs(sn, headless=False, debug_dump_on_fail=True, require_nonempty_values=True)
    print("\n결과:", result)
