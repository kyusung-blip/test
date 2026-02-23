# ecountenter.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def run_ecount_web_automation(data):
    """
    data: buyprogram.py에서 넘어온 etc_data 딕셔너리
    """
    # 1. 브라우저 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 화면 없이 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 2. 드라이버 실행 (환경에 따라 경로 설정 필요)
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 3. 이카운트 로그인
        driver.get("https://login.ecount.com/Login/")
        
        # ID/PW 입력 (이카운트 로그인 구조에 맞게 Selector 수정 필요)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "com_code"))).send_keys("회사코드")
        driver.find_element(By.ID, "id").send_keys("아이디")
        driver.find_element(By.ID, "passwd").send_keys("비밀번호")
        driver.find_element(By.ID, "save").click()
        
        # 4. 특정 메뉴 이동 (예: 재고 - 구매입력 - 품목수정 등)
        # 이카운트는 iframe이 많으므로 switch_to.frame 작업이 핵심입니다.
        time.sleep(3) # 페이지 로딩 대기
        
        # 5. API로 입력 불가했던 변수들 입력 로직
        # 예: etc_data['v_c'] (CBM), etc_data['length'] 등 활용
        # driver.find_element(By.XPATH, "필드경로").send_keys(data['v_c'])
        
        # 6. 저장 버튼 클릭
        # driver.find_element(By.ID, "btnSave").click()
        
        return {"status": "success", "message": "ERP 웹 자동화 입력 성공!"}

    except Exception as e:
        return {"status": "error", "message": f"자동화 실패: {str(e)}"}
    
    finally:
        driver.quit()
