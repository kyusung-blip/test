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
    # 자동화 차단 방지용 User-Agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    try:
        status_placeholder.write("🔍 브라우저 엔진 시동 중...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
            options=options
        )
        wait = WebDriverWait(driver, 20)

        # --- 1단계: 로그인 ---
        status_placeholder.write("🔐 이카운트 로그인 페이지 접속...")
        driver.get("https://login.ecount.com/Login/")
        
        # ID Login 탭 활성화 대기 (필요시)
        time.sleep(1)
        
        # 회사코드 입력
        com_code = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="com_code"]')))
        com_code.clear()
        com_code.send_keys("682186")
        
        # ID 입력
        user_id = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="id"]')))
        user_id.clear()
        user_id.send_keys("이규성")
        
        # PW 입력
        user_pw = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="passwd"]')))
        user_pw.clear()
        user_pw.send_keys("dlrbtjd1367!")
        
        # 3. 로그인 버튼 클릭
        status_placeholder.write("🚀 로그인 버튼 클릭 및 세션 대기 중...")
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="save"]')))
        login_btn.click()
        
        # --- 수정된 판정 로직 ---
        # 5초간 기다리며 URL이 바뀌거나 메인 화면 요소가 보이는지 확인
        time.sleep(5) 
        
        # 현재 URL이 로그인 페이지가 아니거나, 'MyPage' 같은 메인 요소가 보이면 성공으로 간주
        is_login_success = False
        if "login" not in driver.current_url.lower():
            is_login_success = True
        else:
            # 혹시 모르니 메인 상단 메뉴(MyPage 등)가 있는지 확인
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'MyPage')]")))
                is_login_success = True
            except:
                is_login_success = False

        if not is_login_success:
            driver.save_screenshot("login_failed_debug.png")
            status_placeholder.image("login_failed_debug.png", caption="로그인 판정 실패 시점")
            return {"status": "error", "message": "❌ 로그인 판정 실패 (정보 확인 필요)"}

        status_placeholder.write("✅ 1. 로그인 성공 확인!")

        # --- 2단계: 구매입력 직접 이동 ---
        status_placeholder.write("🚀 구매입력 페이지로 직접 이동...")
        direct_url = "https://loginad.ecount.com/ec5/view/erp?w_flag=1&ec_req_sid=AD-ETDLqM7TZHHlO#menuType=MENUTREE_000004&menuSeq=MENUTREE_000510&groupSeq=MENUTREE_000031&prgId=E040303&depth=4"
        driver.get(direct_url)
        time.sleep(7) # 전체 페이지 로딩 대기

        # --- 3단계: 프레임 전환 및 입력 ---
        status_placeholder.write("🔄 입력 프레임(iframe) 전환...")
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "EC_FRAME")))
        status_placeholder.write("✅ 2. 구매입력창 진입 성공")

        # 품목코드(VIN) 입력
        status_placeholder.write("📝 품목코드(VIN) 입력 중...")
        vin_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[3]'
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, vin_xpath)))
        driver.execute_script("arguments[0].click();", vin_cell)
        time.sleep(1)
        driver.switch_to.active_element.send_keys(data.get('vin', ''))
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(1.5)
        status_placeholder.write(f"✅ 3. 품목코드 입력 완료: {data.get('vin')}")

        # 수량 입력 (기본값 1)
        status_placeholder.write("🔢 수량 입력 중...")
        qty_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[7]'
        qty_cell = driver.find_element(By.XPATH, qty_xpath)
        driver.execute_script("arguments[0].click();", qty_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write("✅ 4. 수량 입력 완료")

        # 단가 입력
        status_placeholder.write("💰 단가 입력 중...")
        price_str = str(data.get('price', '0'))
        price_val = re.sub(r'[^0-9]', '', price_str)
        if price_val and int(price_val) < 100000: # 만원 단위 보정
            price_val = str(int(price_val) * 10000)

        price_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[8]'
        price_cell = driver.find_element(By.XPATH, price_xpath)
        driver.execute_script("arguments[0].click();", price_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(price_val)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write(f"✅ 5. 단가 입력 완료: {price_val}")

        # --- 4단계: 저장 ---
        status_placeholder.write("💾 전표 저장 중 (F8)...")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        time.sleep(3)
        status_placeholder.write("✅ 6. 모든 작업 완료!")
        
        return {"status": "success", "message": "이카운트 전표 작성이 완료되었습니다."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if 'driver' in locals():
            driver.quit()
