"""
Cyberts 차량 제원 정보 크롤링 모듈

Cyberts 사이트에서 차량 제원 정보를 자동으로 조회합니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time


def fetch_vehicle_specs(spec_num):
    """
    Cyberts 사이트에서 차량 제원 정보를 크롤링합니다.
    
    Args:
        spec_num (str): 제원관리번호
        
    Returns:
        dict: {
            "status": "success" or "error",
            "data": {
                "weight": "차량총중량",
                "length": "길이",
                "width": "너비",
                "height": "높이"
            },
            "message": "에러 메시지 (있을 경우)"
        }
    """
    driver = None
    
    try:
        # spec_num 유효성 검사
        if not spec_num or spec_num.strip() == "":
            return {
                "status": "error",
                "data": {},
                "message": "제원관리번호가 없습니다."
            }
        
        # Chrome 옵션 설정
        options = Options()
        options.add_argument('--headless')  # 백그라운드 실행
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # WebDriver 초기화
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        # Cyberts 사이트 접속
        url = "https://www.cyberts.kr/ts/tis/ism/readTsTisInqireSvcMainView.do"
        driver.get(url)
        
        # 페이지 로딩 대기
        time.sleep(2)
        
        # 제원관리번호 입력 필드 찾기
        try:
            spec_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="sFomConfmNo"]'))
            )
            spec_input.clear()
            spec_input.send_keys(spec_num)
        except TimeoutException:
            return {
                "status": "error",
                "data": {},
                "message": "제원관리번호 입력 필드를 찾을 수 없습니다."
            }
        
        # 조회 버튼 클릭
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="btnSearch"]'))
            )
            search_button.click()
        except TimeoutException:
            return {
                "status": "error",
                "data": {},
                "message": "조회 버튼을 찾을 수 없거나 클릭할 수 없습니다."
            }
        
        # 결과 로딩 대기 (차량총중량 필드가 나타날 때까지)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "txtCarTotWt"))
            )
            # 추가 대기 시간 (데이터 완전히 로딩되도록)
            time.sleep(2)
        except TimeoutException:
            return {
                "status": "error",
                "data": {},
                "message": "조회 결과를 불러올 수 없습니다. 제원관리번호를 확인해주세요."
            }
        
        # 차량 제원 정보 크롤링
        try:
            weight_element = driver.find_element(By.ID, "txtCarTotWt")
            length_element = driver.find_element(By.ID, "txtObssLt")
            width_element = driver.find_element(By.ID, "txtLpirLt")
            height_element = driver.find_element(By.ID, "txtObssHg")
            
            # value 속성에서 값 가져오기
            weight = weight_element.get_attribute("value") or ""
            length = length_element.get_attribute("value") or ""
            width = width_element.get_attribute("value") or ""
            height = height_element.get_attribute("value") or ""
            
            return {
                "status": "success",
                "data": {
                    "weight": weight,
                    "length": length,
                    "width": width,
                    "height": height
                },
                "message": "조회 성공"
            }
            
        except NoSuchElementException as e:
            return {
                "status": "error",
                "data": {},
                "message": f"차량 제원 필드를 찾을 수 없습니다: {str(e)}"
            }
    
    except WebDriverException as e:
        return {
            "status": "error",
            "data": {},
            "message": f"WebDriver 오류: {str(e)}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "data": {},
            "message": f"알 수 없는 오류: {str(e)}"
        }
    
    finally:
        # WebDriver 종료
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    # 테스트 코드
    test_spec_num = input("제원관리번호를 입력하세요: ")
    result = fetch_vehicle_specs(test_spec_num)
    print(f"\n결과: {result}")
