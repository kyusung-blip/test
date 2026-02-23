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

def run_ecount_web_automation(data, status_placeholder):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        status_placeholder.write("🔍 브라우저 실행 중...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
            options=options
        )
        wait = WebDriverWait(driver, 20)

        # 1. 로그인
        status_placeholder.write("🔐 로그인 시도 중...")
        driver.get("https://login.ecount.com/Login/")
        wait.until(EC.presence_of_element_located((By.ID, "com_code"))).send_keys("682186")
        driver.find_element(By.ID, "id").send_keys("이규성")
        driver.find_element(By.ID, "passwd").send_keys("dlrbtjd1367!")
        driver.find_element(By.ID, "save").click()
        time.sleep(3)
        status_placeholder.write("✅ 1. 로그인 완료")

    try:
        # --- 로그인 직후 팝업 닫기 (이카운트는 팝업이 메뉴 클릭을 방해할 수 있음) ---
        status_placeholder.write("📌 공지사항 팝업 체크 중...")
        try:
            # 모든 팝업 닫기 버튼(보통 클래스명이나 특정 ID) 시도
            close_btns = driver.find_elements(By.XPATH, "//button[contains(text(), '닫기')]")
            for btn in close_btns:
                btn.click()
        except:
            pass

        # 2. 메뉴 순차 클릭 로직
        status_placeholder.write("📂 메뉴 경로 이동 중...")
        
        # 재고 I 클릭
        menu1 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link_depth1_MENUTREE_000004"]')))
        menu1.click()
        time.sleep(1)

        # 구매관리 클릭
        menu2 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link_depth2_MENUTREE_000031"]')))
        menu2.click()
        time.sleep(1)

        # 구매입력 클릭
        menu3 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link_depth4_MENUTREE_000510"]')))
        menu3.click()
        status_placeholder.write("✅ 2. 구매입력 메뉴 진입 성공")
        
        # --- 중요: 메뉴 클릭 후 새로운 프레임이 뜰 때까지 대기 ---
        time.sleep(3)

        # 3. 품목코드(VIN) 입력
        status_placeholder.write("📝 품목코드(VIN) 입력 중...")
        vin_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[3]'
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, vin_xpath)))
        driver.execute_script("arguments[0].click();", vin_cell)
        time.sleep(1)
        driver.switch_to.active_element.send_keys(data.get('vin', ''))
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write(f"✅ 3. 품목코드 입력 완료 ({data.get('vin')})")
        time.sleep(1)

        # 4. 수량 입력
        status_placeholder.write("🔢 수량 입력 중...")
        qty_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[7]'
        qty_cell = driver.find_element(By.XPATH, qty_xpath)
        driver.execute_script("arguments[0].click();", qty_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write("✅ 4. 수량 입력 완료 (1)")

        # 5. 단가 입력
        status_placeholder.write("💰 단가 입력 중...")
        price_str = str(data.get('price', '0'))
        price_val = re.sub(r'[^0-9]', '', price_str)
        if price_val and int(price_val) < 100000:
            price_val = str(int(price_val) * 10000)

        price_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[8]'
        price_cell = driver.find_element(By.XPATH, price_xpath)
        driver.execute_script("arguments[0].click();", price_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(price_val)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write(f"✅ 5. 단가 입력 완료 ({price_val})")

        # 6. 저장
        status_placeholder.write("💾 저장 중 (F8)...")
        time.sleep(1)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        time.sleep(3)
        status_placeholder.write("✅ 6. 저장 작업 완료!")
        
        return {"status": "success", "message": "모든 작업이 완료되었습니다."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    finally:
        if 'driver' in locals():
            driver.quit()
