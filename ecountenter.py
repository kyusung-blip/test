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
    # options.add_argument("--headless")  # 테스트 중에는 주석 처리하여 화면을 확인하세요.
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # 1. 로그인
        driver.get("https://login.ecount.com/Login/")
        wait.until(EC.presence_of_element_located((By.ID, "com_code"))).send_keys("682186")
        driver.find_element(By.ID, "id").send_keys("이규성")
        driver.find_element(By.ID, "passwd").send_keys("dlrbtjd1367!")
        driver.find_element(By.ID, "save").click()
        time.sleep(3)

        # 2. 구매입력 메뉴로 이동 (URL 직접 접근이 가장 빠릅니다)
        # 일반적인 경로: 재고 -> 구매관리 -> 구매입력
        driver.get("https://login.ecount.com/Inventory/Purchase/Purchase")
        time.sleep(3)

        # 3. 이카운트 특유의 iframe 전환 (구매입력 창은 보통 'EC_FRAME' 혹은 동적 ID)
        # 메인 프레임 찾기
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "EC_FRAME")))

        # 4. 데이터 입력 (그리드 방식 대응)
        # 품목코드 (VIN)
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[3]')))
        vin_cell.click() # 클릭해야 입력 활성화
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(data.get('vin', ''))
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(1)

        # 수량 (기본값 1)
        qty_cell = driver.find_element(By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[7]')
        qty_cell.click()
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)

        # 단가 (Price) - 콤마 제거 후 숫자만 입력
        price_raw = data.get('price', '0').replace(',', '').replace('만원', '').strip()
        # '만원' 단위 처리 (예: 1300 -> 13000000)
        try:
            price_val = str(int(price_raw) * 10000)
        except:
            price_val = price_raw

        price_cell = driver.find_element(By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[8]')
        price_cell.click()
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(price_val)
        driver.switch_to.active_element.send_keys(Keys.ENTER)

        # 5. 저장 (F8 키 전송 또는 저장 버튼 클릭)
        time.sleep(1)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        
        # 저장 완료 대기
        time.sleep(2)
        
        return {"status": "success", "message": "이카운트 웹 구매입력 완료!"}

    except Exception as e:
        return {"status": "error", "message": f"오류 발생: {str(e)}"}
    
    finally:
        driver.quit()
