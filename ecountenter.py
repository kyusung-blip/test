# ecountenter.py
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_ecount_web_automation(data):
    options = Options()
    
    # --- 서버 배포용 필수 설정 ---
    options.add_argument("--headless")  # 서버에서는 화면이 없으므로 무조건 headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # Streamlit Cloud의 chromium 경로 지정
    options.binary_location = "/usr/bin/chromium" 
    
    # 서비스 설정 (드라이버 경로)
    service = Service("/usr/bin/chromedriver")
    
    try:
        # 드라이버 실행 시 service와 options를 함께 전달
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)

        # 1. 로그인
        driver.get("https://login.ecount.com/Login/")
        wait.until(EC.presence_of_element_located((By.ID, "com_code"))).send_keys("682186")
        driver.find_element(By.ID, "id").send_keys("이규성")
        driver.find_element(By.ID, "passwd").send_keys("dlrbtjd1367!")
        driver.find_element(By.ID, "save").click()
        time.sleep(3)

        # 2. 구매입력 메뉴 이동
        driver.get("https://login.ecount.com/Inventory/Purchase/Purchase")
        time.sleep(3)

        # 3. 프레임 전환 (이카운트는 대개 EC_FRAME 이라는 ID를 씁니다)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "EC_FRAME")))

        # 4. 데이터 입력
        # 품목코드
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[3]')))
        vin_cell.click()
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(data.get('vin', ''))
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(1)

        # 수량
        qty_cell = driver.find_element(By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[7]')
        qty_cell.click()
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)

        # 단가 (숫자만 추출)
        import re
        price_str = str(data.get('price', '0'))
        price_val = re.sub(r'[^0-9]', '', price_str) # "1,300만원" -> "1300"
        
        # 만원 단위라면 뒤에 0000 추가 (필요 시 수정)
        if int(price_val) < 100000: 
            price_val = str(int(price_val) * 10000)

        price_cell = driver.find_element(By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[8]')
        price_cell.click()
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(price_val)
        driver.switch_to.active_element.send_keys(Keys.ENTER)

        # 5. 저장 (F8)
        time.sleep(1)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        time.sleep(3) # 저장 처리 대기
        
        return {"status": "success", "message": "✅ 이카운트 웹 구매입력 성공!"}

    except Exception as e:
        return {"status": "error", "message": f"❌ 오류 발생: {str(e)}"}
    
    finally:
        if 'driver' in locals():
            driver.quit()
