import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

def run_ecount_web_automation(data):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Streamlit Cloud 환경에서 드라이버를 자동으로 찾도록 설정
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
            options=options
        )
    except:
        # 위 방식이 실패할 경우 기존의 고정 경로 시도
        service = Service("/usr/bin/chromedriver")
        options.binary_location = "/usr/bin/chromium"
        driver = webdriver.Chrome(service=service, options=options)

    wait = WebDriverWait(driver, 20)

    try:
        # 1. 로그인
        driver.get("https://login.ecount.com/Login/")
        wait.until(EC.presence_of_element_located((By.ID, "com_code"))).send_keys("682186")
        driver.find_element(By.ID, "id").send_keys("이규성")
        driver.find_element(By.ID, "passwd").send_keys("dlrbtjd1367!")
        driver.find_element(By.ID, "save").click()
        
        # 로그인 완료 대기 (메인 대시보드 로딩)
        time.sleep(5)

        # 2. 구매입력 메뉴 이동 (iframe 밖에서 실행)
        driver.get("https://login.ecount.com/Inventory/Purchase/Purchase")
        time.sleep(5)

        # 3. iframe 전환 (이카운트는 메뉴마다 프레임이 생성됨)
        # 모든 프레임을 뒤져서 EC_FRAME을 찾거나 인덱스로 접근
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "EC_FRAME")))

        # 4. 데이터 입력 - JavaScript 클릭 사용 (더 안정적임)
        # 품목코드 입력
        vin_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[3]'
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, vin_xpath)))
        driver.execute_script("arguments[0].click();", vin_cell) # 자바스크립트로 강제 클릭
        time.sleep(1)
        
        active_input = driver.switch_to.active_element
        active_input.send_keys(data.get('vin', ''))
        active_input.send_keys(Keys.ENTER)
        time.sleep(1.5)

        # 수량 입력 (7번째 칸)
        qty_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[7]'
        qty_cell = driver.find_element(By.XPATH, qty_xpath)
        driver.execute_script("arguments[0].click();", qty_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)

        # 단가 입력 (8번째 칸)
        price_str = str(data.get('price', '0'))
        price_val = re.sub(r'[^0-9]', '', price_str)
        if price_val and int(price_val) < 100000: # 만원 단위 처리
            price_val = str(int(price_val) * 10000)

        price_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[8]'
        price_cell = driver.find_element(By.XPATH, price_xpath)
        driver.execute_script("arguments[0].click();", price_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(price_val)
        driver.switch_to.active_element.send_keys(Keys.ENTER)

        # 5. 저장 (F8 키)
        time.sleep(1)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        time.sleep(3) 
        
        return {"status": "success", "message": "✅ 이카운트 웹 구매입력 성공!"}

    except Exception as e:
        # 에러 발생 시 현재 화면 캡처 (디버깅용 - 필요시)
        # driver.save_screenshot("error_log.png")
        return {"status": "error", "message": f"❌ 오류 발생: {str(e)}"}
    
    finally:
        if 'driver' in locals():
            driver.quit()
