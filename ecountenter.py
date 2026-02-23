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
        
        # 4. 데이터 입력 (SPA 구조 대응)
        status_placeholder.write("📝 입력 구역 로딩 대기 중...")
        
        # [수정 포인트] 10초 대기 대신, 특정 요소가 나타날 때까지 스마트하게 대기
        vin_xpath = "//*[@data-column-id='prod_cd']"
        try:
            # 품목코드(prod_cd) 셀이 나타나고 클릭 가능할 때까지 최대 20초 대기
            vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, vin_xpath)))
            status_placeholder.write("✅ 입력 테이블 로드 완료")
        except Exception as e:
            status_placeholder.write("❌ 페이지 로딩 시간이 초과되었습니다.")
            driver.save_screenshot("loading_timeout.png")
            return {"status": "error", "message": "입력 화면 로딩 실패"}

        # 셀 클릭 및 입력 시작
        driver.execute_script("arguments[0].click();", vin_cell)
        
        # 클릭 후 입력 모드로 전환되는 찰나의 시간 (0.5~1초)은 유지하는 것이 안전합니다.
        time.sleep(1)
        
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
