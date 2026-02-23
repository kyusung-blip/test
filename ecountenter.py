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

         # 4. 데이터 입력 시작 (개별 지정 및 실시간 로그 출력)
        try:
            status_placeholder.write("📝 전체 데이터 입력 프로세스 시작...")
            # 전달받은 전체 데이터의 형태를 잠시 확인 (디버깅용)
            # status_placeholder.write(f"DEBUG: 수신 데이터 키 목록 -> {list(data.keys())}")
            time.sleep(3)

            # --- [구매담당] ---
            val = data.get('username')
            if val:
                status_placeholder.write(f"📍 [구매담당] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[2]/div[2]/div/div/input[1]')))
                el.clear()
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)
            else:
                status_placeholder.write("⚠️ [구매담당] 데이터가 없어 건너뜁니다.")

            # --- [세일즈팀] ---
            val = data.get('sales')
            if val:
                status_placeholder.write(f"📍 [세일즈팀] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[3]/div[2]/div/div/input')))
                el.clear()
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [Buyer] ---
            val = data.get('buyer')
            if val:
                status_placeholder.write(f"📍 [Buyer] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[4]/div[2]/div/div/input')))
                el.clear()
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [국가코드] ---
            val = data.get('country')
            if val:
                status_placeholder.write(f"📍 [국가코드] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[5]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [YEAR] ---
            val = data.get('year')
            if val:
                status_placeholder.write(f"📍 [YEAR] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[7]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [BRAND] ---
            val = data.get('brand')
            if val:
                status_placeholder.write(f"📍 [BRAND] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[8]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [MODEL] ---
            val = data.get('car_name_remit')
            if val:
                status_placeholder.write(f"📍 [MODEL] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[9]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [PLATE] ---
            val = data.get('plate')
            if val:
                status_placeholder.write(f"📍 [PLATE] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[10]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [VIN] ---
            val = data.get('vin')
            if val:
                status_placeholder.write(f"📍 [VIN] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[11]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [COLOR] ---
            val = data.get('color')
            if val:
                status_placeholder.write(f"📍 [COLOR] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[12]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [km] ---
            val = data.get('km')
            if val:
                status_placeholder.write(f"📍 [km] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[13]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [위치] ---
            val = data.get('region')
            if val:
                status_placeholder.write(f"📍 [위치] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[14]/div[2]/div/div/input')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)

            # --- [거래처] ---
            val = data.get('bizcl_num')
            if val:
                status_placeholder.write(f"📍 [거래처] 입력 시도: {val}")
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[19]/div[2]/div/div/input[1]')))
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(2) # 거래처 검색 팝업 처리 대기
                
            # --- [psource] 추가 ---
            val = data.get('psource')
            if val:
                status_placeholder.write(f"📍 [psource] 입력 시도: {val}")
                # 지정하신 XPath 사용
                el = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainPage"]/div[2]/div[4]/div[1]/ul/li[23]/div[2]/div/div/input')))
                
                # 안정적인 입력을 위해 클릭 후 기존 내용 삭제
                driver.execute_script("arguments[0].click();", el)
                el.send_keys(Keys.CONTROL + "a")
                el.send_keys(Keys.BACKSPACE)
                
                el.send_keys(str(val))
                el.send_keys(Keys.ENTER)
                time.sleep(0.5)
                # 혹시 모를 검색 팝업 방지
                driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            else:
                status_placeholder.write("⚠️ [psource] 데이터가 없어 건너뜁니다.")

            # --- [하단 그리드: 품목/수량/단가] ---
            status_placeholder.write("📊 그리드 입력 단계 진입...")
            
            # 1. 첫 번째 행: 차량 단가 (Price2)
            prod_val = data.get('vin') # 품목코드에 vin 사용
            status_placeholder.write(f"📍 [그리드 Row 1] 차량 품목 입력: {prod_val}")
            prod_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[3]/span')))
            driver.execute_script("arguments[0].click();", prod_cell)
            time.sleep(1.5)
            driver.switch_to.active_element.send_keys(str(prod_val))
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(2)
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)

            # 수량 (1)
            qty_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[7]/span')))
            driver.execute_script("arguments[0].click();", qty_cell)
            time.sleep(1)
            active_el = driver.switch_to.active_element
            active_el.send_keys(Keys.CONTROL + "a")
            active_el.send_keys(Keys.BACKSPACE)
            active_el.send_keys("1")
            active_el.send_keys(Keys.ENTER)
            time.sleep(1)

            # 단가 (Price2)
            price_val = re.sub(r'[^0-9]', '', str(data.get('price2', '0')))
            price_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[8]/span[2]')))
            driver.execute_script("arguments[0].click();", price_cell)
            time.sleep(1)
            driver.switch_to.active_element.send_keys(price_val)
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(1)

            # ---------------------------------------------------------
            # 2. 두 번째 행: 계산서X 처리
            # ---------------------------------------------------------
            contract2_x_val = int(data.get('contract2_x', 0))
            if contract2_x_val > 0:
                status_placeholder.write(f"📍 [그리드 Row 2] 계산서X 입력 중: {contract2_x_val}")
                
                # 품목코드 입력 (Row 2)
                prod_val = data.get('vin') # 품목코드에 vin 사용
                status_placeholder.write(f"📍 [그리드 Row 2] 차량 품목 입력: {prod_val}")
                prod_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[2]/td[3]/span')))
                driver.execute_script("arguments[0].click();", prod_cell)
                time.sleep(1.5)
                driver.switch_to.active_element.send_keys(str(prod_val))
                driver.switch_to.active_element.send_keys(Keys.ENTER)
                time.sleep(2)
                driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            
                # 수량 (1)
                qty_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[2]/td[7]/span')))
                driver.execute_script("arguments[0].click();", qty_cell)
                time.sleep(1)
                active_el = driver.switch_to.active_element
                active_el.send_keys(Keys.CONTROL + "a")
                active_el.send_keys(Keys.BACKSPACE)
                active_el.send_keys("1")
                active_el.send_keys(Keys.ENTER)
                time.sleep(1)

                # 공급가액 입력 (Row 2) - fee2 값
                contract2_x_amt_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[2]/td[9]/span')))
                driver.execute_script("arguments[0].click();", contract2_x_amt_cell)
                time.sleep(0.5)
                driver.switch_to.active_element.send_keys(str(contract2_x_val))
                driver.switch_to.active_element.send_keys(Keys.ENTER)

                # 부가세 입력 (Row 2) - 0 세팅
                contract2_x_vat_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[2]/td[10]/span')))
                driver.execute_script("arguments[0].click();", contract2_x_vat_cell)
                time.sleep(0.5)
                driver.switch_to.active_element.send_keys("0")
                driver.switch_to.active_element.send_keys(Keys.ENTER)
                time.sleep(1)
            else:
                status_placeholder.write("⏭️ [계산서X] 값이 0이거나 없어 건너뜁니다.")

            # ---------------------------------------------------------
            # 3. 세 번째 행: 매도비 처리
            # ---------------------------------------------------------
            fee2_val = int(data.get('fee2', 0))
            if fee2_val > 0:
                status_placeholder.write(f"📍 [그리드 Row 3] 매도비 입력 중: {fee2_val}")
                
                # 품목코드 입력 (Row 2)
                prod_val = data.get('vin') # 품목코드에 vin 사용
                status_placeholder.write(f"📍 [그리드 Row 3] 차량 품목 입력: {prod_val}")
                prod_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[3]/td[3]/span')))
                driver.execute_script("arguments[0].click();", prod_cell)
                time.sleep(1.5)
                driver.switch_to.active_element.send_keys(str(prod_val))
                driver.switch_to.active_element.send_keys(Keys.ENTER)
                time.sleep(2)
                driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            
                # 수량 (1)
                qty_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[3]/td[7]/span')))
                driver.execute_script("arguments[0].click();", qty_cell)
                time.sleep(1)
                active_el = driver.switch_to.active_element
                active_el.send_keys(Keys.CONTROL + "a")
                active_el.send_keys(Keys.BACKSPACE)
                active_el.send_keys("1")
                active_el.send_keys(Keys.ENTER)
                time.sleep(1)

                # 공급가액 입력 (Row 3) - fee2 값
                con_amt_cell = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="grid-main"]/tbody/tr[3]/td[8]/span[2]')))
                driver.execute_script("arguments[0].click();", con_amt_cell)
                time.sleep(0.5)
                driver.switch_to.active_element.send_keys(str(fee2_val))
                driver.switch_to.active_element.send_keys(Keys.ENTER)
                time.sleep(1)
            else:
                status_placeholder.write("⏭️ [매도비] 값이 0이거나 없어 건너뜁니다.")

            # --- [최종 저장] ---
            status_placeholder.write("💾 저장 버튼 클릭 중...")
            save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="group3slipSave"]')))
            driver.execute_script("arguments[0].click();", save_btn)
            time.sleep(5)
            
            return {"status": "success", "message": "모든 데이터가 입력되고 저장되었습니다."}

        except Exception as e:
            # 실패 시 현재까지의 진행 상황 파악을 위해 스크린샷 저장
            driver.save_screenshot("debug_input_stage.png")
            return {"status": "error", "message": f"입력 도중 오류 발생: {type(e).__name__}"}

    except Exception as e:
        return {"status": "error", "message": f"시스템 오류: {str(e)[:50]}"}
    
    finally:
        if driver:
            driver.quit()
