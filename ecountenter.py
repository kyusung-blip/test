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

                # 4. 데이터 입력 시작
        try:
            # [핵심] 현재 눈에 보이는(display: block) 탭 내부의 그리드만 찾도록 XPath 수정
            active_grid_path = "//div[contains(@class, 'tab-pane') and not(contains(@style, 'display: none'))]//*[@id='grid-main']"
            
            # 1. 품목코드 입력
            prod_xpath = f"{active_grid_path}/tbody/tr[1]/td[3]/span"
            prod_cell = wait.until(EC.element_to_be_clickable((By.XPATH, prod_xpath)))
            driver.execute_script("arguments[0].click();", prod_cell)
            time.sleep(2) # 입력 모드 전환 및 혹시 모를 팝업 대기
        
            # 입력창이 활성화되면 값 입력
            active_el = driver.switch_to.active_element
            active_el.send_keys(data.get('vin', ''))
            time.sleep(1)
            active_el.send_keys(Keys.ENTER)
            time.sleep(2) # 검색 결과 반영 대기
        
            # [팁] 만약 품목 입력 후 팝업이 남아있다면 ESC를 눌러 닫아줘야 다음 단계가 진행됩니다.
            active_el.send_keys(Keys.ESCAPE) 
            time.sleep(0.5)
        
            # 2. 수량 입력
            qty_xpath = f"{active_grid_path}/tbody/tr[1]/td[7]/span"
            qty_cell = wait.until(EC.element_to_be_clickable((By.XPATH, qty_xpath)))
            driver.execute_script("arguments[0].click();", qty_cell)
            time.sleep(1)
            driver.switch_to.active_element.send_keys("1")
            driver.switch_to.active_element.send_keys(Keys.ENTER)
        
        except Exception as e:
            # 에러 발생 시 Message 외에 구체적인 클래스명 출력
            print(f"상세 에러 타입: {type(e).__name__}") 
            driver.save_screenshot("debug_last_frame.png")
    finally:
        if 'driver' in locals():
            driver.quit()
