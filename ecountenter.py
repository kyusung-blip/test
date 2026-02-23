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
        
        # 2. 로그인 완료 판정 및 메뉴 이동 시작
        status_placeholder.write("⏳ 로그인 완료 대기 중...")
        try:
            # 메인 페이지 로고가 나타날 때까지 대기하여 세션 확정
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.company-logo")))
            time.sleep(2)  # 로그인 후 첫 화면 안착 대기
            status_placeholder.write("✅ 로그인 성공")
        except:
            return {"status": "error", "message": "로그인 후 메인 화면 진입에 실패했습니다."}

        # 3. 메뉴 클릭 단계별 이동
        try:
            # (1) 재고I 클릭 (나올 때까지 대기 후 클릭)
            status_placeholder.write("📂 '재고I' 메뉴 클릭 중...")
            inventory_1 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link_depth1_MENUTREE_000004"]')))
            inventory_1.click()
            
            # (2) 구매관리 클릭
            status_placeholder.write("📁 '구매관리' 클릭 중...")
            purchase_mgmt = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link_depth2_MENUTREE_000031"]')))
            purchase_mgmt.click()
            
            # (3) 1초 대기 후 구매입력 클릭
            status_placeholder.write("📄 '구매입력' 이동 중 (1초 대기)...")
            time.sleep(1)
            purchase_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="link_depth4_MENUTREE_000510"]')))
            purchase_input.click()
            
            status_placeholder.write("✅ 구매입력 페이지 도달 성공")
            
        except Exception as e:
            driver.save_screenshot("menu_click_error.png")
            return {"status": "error", "message": f"메뉴 이동 중 오류 발생: {str(e)[:50]}"}

         # 4. 데이터 입력 시작 (마스터 정보 + 그리드 정보)
        try:
            status_placeholder.write("📝 전체 데이터 입력 프로세스 시작...")
            time.sleep(3) # 페이지 로딩 안정화 대기

            # --- [Part 1] 상단 마스터 정보 입력 영역 ---
            # 입력 편의를 위한 매핑 설정
            master_fields = [
                ("구매담당", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[2]/div[2]/div/div/input[1]', data.get('username')),
                ("세일즈팀", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[3]/div[2]/div/div/input', data.get('sales')),
                ("Buyer", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[4]/div[2]/div/div/input', data.get('buyer')),
                ("국가코드", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[5]/div[2]/div/div/input', data.get('country')),
                ("YEAR", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[7]/div[2]/div/div/input', data.get('year')),
                ("BRAND", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[8]/div[2]/div/div/input', data.get('brand')),
                ("MODEL", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[9]/div[2]/div/div/input', data.get('car_name_remit')),
                ("PLATE", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[10]/div[2]/div/div/input', data.get('plate')),
                ("VIN", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[11]/div[2]/div/div/input', data.get('vin')),
                ("COLOR", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[12]/div[2]/div/div/input', data.get('color')),
                ("km", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[13]/div[2]/div/div/input', data.get('km')),
                ("위치", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[14]/div[2]/div/div/input', data.get('region')),
                ("거래처", '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[19]/div[2]/div/div/input[1]', data.get('biz_num'))
            ]

            for label, xpath, value in master_fields:
                if value:
                    status_placeholder.write(f"🔹 {label} 입력 중...")
                    field = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    field.clear()
                    field.send_keys(str(value))
                    field.send_keys(Keys.ENTER)
                    time.sleep(0.7) # 필드 간 입력 간격

            # --- [Part 2] 하단 그리드 정보 입력 영역 ---
            status_placeholder.write("📊 그리드 품목 정보 입력 중...")
            
            # 1. 품목코드 (이미 검증된 로직)
            prod_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[3]/span'
            prod_cell = wait.until(EC.presence_of_element_located((By.XPATH, prod_xpath)))
            driver.execute_script("arguments[0].click();", prod_cell)
            time.sleep(1.5)
            driver.switch_to.active_element.send_keys(data.get('vin', '')) # 품목코드로 vin 사용
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(2)
            driver.switch_to.active_element.send_keys(Keys.ESCAPE) # 팝업 방지

            # 2. 수량 (1 고정)
            qty_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[7]/span'
            qty_cell = wait.until(EC.presence_of_element_located((By.XPATH, qty_xpath)))
            driver.execute_script("arguments[0].click();", qty_cell)
            time.sleep(1)
            active_el = driver.switch_to.active_element
            active_el.send_keys(Keys.CONTROL + "a")
            active_el.send_keys(Keys.BACKSPACE)
            active_el.send_keys("1")
            active_el.send_keys(Keys.ENTER)
            time.sleep(1)

            # 3. 단가 (price)
            status_placeholder.write("🔹 단가 입력 중...")
            price_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[8]/span[2]'
            price_cell = wait.until(EC.presence_of_element_located((By.XPATH, price_xpath)))
            driver.execute_script("arguments[0].click();", price_cell)
            time.sleep(1)
            
            # 단가에서 숫자만 추출하여 입력
            price_val = re.sub(r'[^0-9]', '', str(data.get('price', '0')))
            driver.switch_to.active_element.send_keys(price_val)
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(1)

            # --- [Part 3] 최종 저장 ---
            status_placeholder.write("💾 전표 저장 시도 중...")
            save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="group3slipSave"]')))
            driver.execute_script("arguments[0].click();", save_btn)
            
            # 저장 후 완료 팝업이나 화면 전환 대기
            time.sleep(5)
            driver.save_screenshot("final_record.png")
            status_placeholder.image("final_record.png", caption="최종 입력 완료 상태")

            return {"status": "success", "message": "모든 필드 입력 및 전표 저장 완료!"}

        except Exception as e:
            driver.save_screenshot("error_detail.png")
            return {"status": "error", "message": f"입력 도중 오류 발생: {type(e).__name__}"}

    except Exception as e:
        return {"status": "error", "message": f"시스템 오류: {str(e)[:50]}"}
    
    finally:
        if driver:
            driver.quit()
