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

        # 4. 데이터 입력 (그리드 직접 타격)
        status_placeholder.write("📝 그리드 입력 시작...")

        try:
            # --- (1) 품목코드 입력 ---
            status_placeholder.write("🔹 품목코드 입력 중...")
            prod_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[3]/span'
            prod_cell = wait.until(EC.element_to_be_clickable((By.XPATH, prod_xpath)))
            driver.execute_script("arguments[0].click();", prod_cell)
            time.sleep(1.5) # 알려주신 1.5초 대기
            
            # 활성화된 입력창에 값 전송
            driver.switch_to.active_element.send_keys(data.get('vin', ''))
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(1) # 엔터 후 그리드 안정화

            # --- (2) 수량 입력 ---
            status_placeholder.write("🔹 수량 입력 중...")
            qty_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[7]/span'
            qty_cell = wait.until(EC.element_to_be_clickable((By.XPATH, qty_xpath)))
            driver.execute_script("arguments[0].click();", qty_cell)
            time.sleep(0.8)
            
            driver.switch_to.active_element.send_keys("1")
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(0.5)

            # --- (3) 단가 입력 ---
            status_placeholder.write("🔹 단가 입력 중...")
            price_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[8]/span'
            price_cell = wait.until(EC.element_to_be_clickable((By.XPATH, price_xpath)))
            driver.execute_script("arguments[0].click();", price_cell)
            time.sleep(0.8)
            
            # 단가 계산 (기존 로직 유지)
            price_val = re.sub(r'[^0-9]', '', str(data.get('price', '0')))
            driver.switch_to.active_element.send_keys(price_val)
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            
            status_placeholder.write("✅ 그리드 데이터 입력 완료")

        except Exception as e:
            driver.save_screenshot("input_error.png")
            return {"status": "error", "message": f"입력 단계 오류: {str(e)[:50]}"}

        # 5. 저장 (알려주신 전용 ID 클릭)
        status_placeholder.write("💾 전표 저장 중...")
        try:
            save_btn_xpath = '//*[@id="group3slipSave"]'
            save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, save_btn_xpath)))
            
            # 다른 팝업이 가리고 있을 수 있으므로 JS로 강제 클릭
            driver.execute_script("arguments[0].click();", save_btn)
            
            # 저장 후 서버 응답을 위해 충분히 대기
            time.sleep(5) 
            driver.save_screenshot("final_result.png")
            status_placeholder.image("final_result.png", caption="최종 저장 결과")
            
            return {"status": "success", "message": "성공적으로 저장되었습니다."}
        except Exception as e:
            return {"status": "error", "message": f"저장 실패: {str(e)[:50]}"}
    finally:
        if 'driver' in locals():
            driver.quit()
