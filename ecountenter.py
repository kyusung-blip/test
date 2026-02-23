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

    try:
        status_placeholder.write("🔍 브라우저 실행 중...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
            options=options
        )
        wait = WebDriverWait(driver, 20)

        # 1. 'ID Login' 탭을 먼저 클릭 (스크린샷 기반 활성화 보장)
        try:
            id_login_tab = wait.until(EC.element_to_be_clickable((By.ID, "liId")))
            id_login_tab.click()
            time.sleep(0.5)
        except:
            pass # 이미 선택되어 있을 수 있음

        # 2. 정보 입력
        status_placeholder.write("📝 로그인 정보 입력 중...")
        wait.until(EC.presence_of_element_located((By.ID, "com_code"))).send_keys("682186")
        driver.find_element(By.ID, "id").send_keys("이규성")
        
        pw_field = driver.find_element(By.ID, "passwd")
        pw_field.send_keys("dlrbtjd1367!")
        
        # 3. 로그인 시도 (버튼 클릭 대신 엔터 키 사용이 더 확실할 때가 많음)
        time.sleep(1)
        pw_field.send_keys(Keys.ENTER)
        
        # 4. 로그인 성공 여부 체크 (URL 변화 확인)
        status_placeholder.write("⏳ 로그인 처리 대기 중...")
        time.sleep(5) 

        # 현재 URL이 여전히 'login'을 포함하고 있다면 실패로 간주
        if "login" in driver.current_url.lower():
            # 실패 원인 분석을 위해 화면 캡처
            driver.save_screenshot("login_failed.png")
            status_placeholder.image("login_failed.png", caption="로그인 실패 상태")
            return {"status": "error", "message": "❌ 로그인을 완료하지 못했습니다. ID/PW를 다시 확인하거나 보안 문자가 떴는지 확인해주세요."}

        status_placeholder.write("✅ 1. 로그인 성공")

        # 2. 구매입력 URL로 직접 이동
        status_placeholder.write("🚀 구매입력 페이지로 직접 이동 중...")
        direct_url = "https://loginad.ecount.com/ec5/view/erp?w_flag=1&ec_req_sid=AD-ETDLqM7TZHHlO#menuType=MENUTREE_000004&menuSeq=MENUTREE_000510&groupSeq=MENUTREE_000031&prgId=E040303&depth=4"
        driver.get(direct_url)
        
        # 페이지 전체가 로드될 때까지 충분히 대기
        time.sleep(6) 

        # 3. 프레임 전환 (핵심 단계)
        status_placeholder.write("🔄 입력창(iframe) 활성화 중...")
        driver.switch_to.default_content()
        
        # EC_FRAME이 나타날 때까지 대기 후 전환
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "EC_FRAME")))
            status_placeholder.write("✅ 2. 구매입력창 진입 성공")
        except:
            # 혹시라도 프레임 ID가 다를 경우를 대비해 스크린샷 캡처
            driver.save_screenshot("frame_error.png")
            status_placeholder.image("frame_error.png", caption="프레임 전환 실패 시 화면")
            return {"status": "error", "message": "입력 프레임을 찾을 수 없습니다."}

        # 4. 데이터 입력 (JS 클릭 후 활성 요소에 입력)
        status_placeholder.write("📝 품목코드(VIN) 입력 중...")
        vin_xpath = '//*[@id="grid-main"]/tbody/tr[1]/td[3]'
        vin_cell = wait.until(EC.element_to_be_clickable((By.XPATH, vin_xpath)))
        driver.execute_script("arguments[0].click();", vin_cell)
        time.sleep(1)
        
        driver.switch_to.active_element.send_keys(data.get('vin', ''))
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        time.sleep(1.5)
        status_placeholder.write(f"✅ 3. 품목코드 입력 완료: {data.get('vin')}")

        # 5. 수량(7) 및 단가(8) 입력
        # 수량
        qty_cell = driver.find_element(By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[7]')
        driver.execute_script("arguments[0].click();", qty_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys("1")
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write("✅ 4. 수량 입력 완료")

        # 단가 (만원 단위 환산 로직 포함)
        price_str = str(data.get('price', '0'))
        price_val = re.sub(r'[^0-9]', '', price_str)
        if price_val and int(price_val) < 100000:
            price_val = str(int(price_val) * 10000)

        price_cell = driver.find_element(By.XPATH, '//*[@id="grid-main"]/tbody/tr[1]/td[8]')
        driver.execute_script("arguments[0].click();", price_cell)
        time.sleep(0.5)
        driver.switch_to.active_element.send_keys(price_val)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        status_placeholder.write(f"✅ 5. 단가 입력 완료: {price_val}")

        # 6. 저장 (F8)
        status_placeholder.write("💾 전표 저장 중...")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F8)
        time.sleep(3)
        status_placeholder.write("✅ 6. 저장 완료!")
        
        return {"status": "success", "message": "이카운트 입력이 성공적으로 마무리되었습니다."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    finally:
        if 'driver' in locals():
            driver.quit()
