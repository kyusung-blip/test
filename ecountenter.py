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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    try:
        status_placeholder.write("🔍 브라우저 엔진 시동 중...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
            options=options
        )
        wait = WebDriverWait(driver, 20)

        # 1. 로그인 단계 (요청하신 XPath 적용)
        status_placeholder.write("🔐 이카운트 로그인 시도 중...")
        driver.get("https://login.ecount.com/Login/")
        
        # 회사코드 입력 (XPath)
        com_code_el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="com_code"]')))
        com_code_el.clear()
        com_code_el.send_keys("682186")
        
        # ID 입력 (XPath)
        id_el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="id"]')))
        id_el.clear()
        id_el.send_keys("이규성")
        
        # PW 입력 (XPath)
        pw_el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="passwd"]')))
        pw_el.clear()
        pw_el.send_keys("dlrbtjd1367!")
        
        # 로그인 버튼 클릭 (XPath)
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="save"]')))
        login_btn.click()
        
        status_placeholder.write("⏳ 세션 승인 대기 중...")
        time.sleep(5)

        if "login" in driver.current_url.lower():
            driver.save_screenshot("login_error.png")
            status_placeholder.image("login_error.png", caption="로그인 실패 화면")
            return {"status": "error", "message": "로그인 실패 (ID/PW 또는 보안문자 확인)"}
        status_placeholder.write("✅ 1. 로그인 성공")

        # 2. 구매입력 URL로 직접 이동
        status_placeholder.write("🚀 구매입력 페이지 이동 중...")
        direct_url = "https://loginad.ecount.com/ec5/view/erp?w_flag=1&ec_req_sid=AD-ETDLqM7TZHHlO#menuType=MENUTREE_000004&menuSeq=MENUTREE_000510&groupSeq=MENUTREE_000031&prgId=E040303&depth=4"
        driver.get(direct_url)
        time.sleep(8) 

        # 3. 데이터 입력 (SPA 구조 - iframe 없음)
        status_placeholder.write("📝 데이터 입력 구역 포착 중...")
        driver.switch_to.default_content() 

        # A. 품목코드(VIN) 입력
        # 사용자님이 제공한 span 구조: data-column-id='prod_cd' 활용
        vin_xpath = "//*[@data-column-id='prod_cd']"
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, vin_xpath)))
        driver.execute_script("arguments[0].click();", vin_cell)
        time.sleep(1.5) # 입력 모드 전환 대기
        
        driver.switch_to.active_element.send_keys(data.get('vin', ''))
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write(f"✅ 2. 품목코드 입력 완료: {data.get('vin')}")
        time.sleep(1)

        # B. 수량 입력
        qty_xpath = "//*[@data-column-id='qty']"
        qty_cell = driver.find_element(By.XPATH, qty_xpath)
        driver.execute_script("arguments[0].click();", qty_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write("✅ 3. 수량 입력 완료 (1)")

        # C. 단가 입력
        price_str = str(data.get('price', '0'))
        price_val = re.sub(r'[^0-9]', '', price_str)
        if price_val and int(price_val) < 100000:
            price_val = str(int(price_val) * 10000)

        price_xpath = "//*[@data-column-id='price']"
        price_cell = driver.find_element(By.XPATH, price_xpath)
        driver.execute_script("arguments[0].click();", price_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(price_val)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write(f"✅ 4. 단가 입력 완료: {price_val}")

        # 4. 저장 (F8)
        status_placeholder.write("💾 전표 저장 중 (F8)...")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        time.sleep(3)
        status_placeholder.write("✅ 5. 저장 완료!")
        
        return {"status": "success", "message": "모든 입력이 성공적으로 마무리되었습니다."}

    except Exception as e:
        driver.save_screenshot("debug_error.png")
        status_placeholder.image("debug_error.png", caption="오류 발생 지점 화면")
        return {"status": "error", "message": str(e)}
    finally:
        if 'driver' in locals():
            driver.quit()
