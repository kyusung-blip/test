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

        # 1. 로그인 단계 (XPath 사용)
        status_placeholder.write("🔐 이카운트 로그인 시도 중...")
        driver.get("https://login.ecount.com/Login/")
        
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="com_code"]'))).send_keys("682186")
        driver.find_element(By.XPATH, '//*[@id="id"]').send_keys("이규성")
        pw_field = driver.find_element(By.XPATH, '//*[@id="passwd"]')
        pw_field.send_keys("dlrbtjd1367!")
        pw_field.send_keys(Keys.ENTER)
        
        # 2. 로고 이미지를 통한 로그인 완료 판정
        status_placeholder.write("⏳ 로그인 완료 확인 중 (로고 탐색)...")
        try:
            # 말씀하신 <img class="company-logo"> 요소가 나타날 때까지 대기
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.company-logo")))
            status_placeholder.write("✅ 1. 로그인 성공 (로고 확인 완료)")
        except:
            # 로고가 안 나오면 현재 화면 캡처 후 종료
            driver.save_screenshot("login_check_error.png")
            status_placeholder.image("login_check_error.png", caption="로그인 판정 실패 시점")
            return {"status": "error", "message": "로그인 후 로고를 찾을 수 없습니다."}

        # 3. 구매입력 URL로 직접 이동
        status_placeholder.write("🚀 구매입력 페이지 이동 중...")
        direct_url = "https://loginad.ecount.com/ec5/view/erp?w_flag=1&ec_req_sid=AD-ETDLqM7TZHHlO#menuType=MENUTREE_000004&menuSeq=MENUTREE_000510&groupSeq=MENUTREE_000031&prgId=E040303&depth=4"
        driver.get(direct_url)
        
        # SPA 구조 데이터 로딩 대기
        time.sleep(10) 

        # 4. 데이터 입력 (SPA 구조 대응)
        status_placeholder.write("📝 입력 구역 포착 중...")
        driver.switch_to.default_content() 

        # 품목코드 입력 (data-column-id='prod_cd')
        vin_xpath = "//*[@data-column-id='prod_cd']"
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, vin_xpath)))
        driver.execute_script("arguments[0].click();", vin_cell)
        time.sleep(1.5)
        
        driver.switch_to.active_element.send_keys(data.get('vin', ''))
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write(f"✅ 2. 품목코드 입력 완료: {data.get('vin')}")

        # 수량 입력 (qty)
        qty_xpath = "//*[@data-column-id='qty']"
        qty_cell = driver.find_element(By.XPATH, qty_xpath)
        driver.execute_script("arguments[0].click();", qty_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write("✅ 3. 수량 입력 완료")

        # 단가 입력 (price)
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

        # 5. 저장 (F8)
        status_placeholder.write("💾 전표 저장 중...")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        time.sleep(3)
        status_placeholder.write("✅ 5. 저장 완료!")
        
        return {"status": "success", "message": "이카운트 입력이 완료되었습니다."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if 'driver' in locals():
            driver.quit()
