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

        # 4. 데이터 입력 (기존 로직 사용)
        status_placeholder.write("📝 입력 구역 로딩 대기 중...")
        
        try:
            # [수정] 현재 'display: block' 상태인 tab-pane 내부에 있는 prod_cd를 찾습니다.
            # 이 XPath는 숨겨진 다른 탭들을 무시하고 현재 눈에 보이는 탭만 타겟팅합니다.
            active_vin_xpath = "//div[contains(@class, 'tab-pane') and not(contains(@style, 'display: none'))]//*[@data-column-id='prod_cd']"
            
            # 1. 요소가 나타날 때까지 대기 (최대 15초)
            vin_cell = wait.until(EC.visibility_of_element_located((By.XPATH, active_vin_xpath)))
            
            # 2. 화면 스크롤 및 클릭 가능 확인
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", vin_cell)
            time.sleep(0.5)
            
            # 3. JS를 사용하여 강제로 클릭 이벤트를 발생시킵니다 (가장 확실함)
            driver.execute_script("arguments[0].click();", vin_cell)
            status_placeholder.write("✅ 입력창 포커스 성공")
            
            # 4. 클릭 후 입력 모드 전환을 위한 찰나의 대기
            time.sleep(1.2)
            
            # 5. 현재 포커스된(active) 요소에 값 입력
            active_el = driver.switch_to.active_element
            active_el.send_keys(data.get('vin', ''))
            active_el.send_keys(Keys.ENTER)
            
            status_placeholder.write(f"✅ 2. 품목코드 입력 완료: {data.get('vin')}")

        except Exception as e:
            # 실패 시 현재 상태를 캡처해서 streamlit에 보여줍니다.
            driver.save_screenshot("debug_view.png")
            status_placeholder.image("debug_view.png", caption="요소 탐색 실패 시점의 화면")
            return {"status": "error", "message": f"요소를 찾을 수 없습니다: {str(e)[:50]}"}

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
