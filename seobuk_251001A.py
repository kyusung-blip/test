import re, time, warnings
import gspread
import streamlit as st
from selenium import webdriver
import time
import os
from selenium.webdriver.common.keys import Keys
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import google_sheet_manager as gm
warnings.filterwarnings(action='ignore')
FILE_NAME = 'SEOBUK PROJECTION'
SHEET_NAME = 'NUEVO PROJECTION#2'

def flush_to_sheet(rows, start_row):
    """지정한 NUEVO PROJECTION#2 시트에 크롤링 데이터 기록"""
    try:
        # 매니저를 통해 특정 시트 가져오기
        ws = gm.get_nuevo_projection_sheet()
        
        # 데이터 업데이트 (기존 로직 유지)
        ws.update(f'A{start_row}', rows, value_input_option='USER_ENTERED')

        # 테두리 서식 설정 등 (기존 로직 유지)
        last_row = start_row + len(rows) - 1
        cell_range = f'A{start_row}:AH{last_row}'
        cell_format = {
            'borders': {
                'top': {'style': 'SOLID'}, 'bottom': {'style': 'SOLID'},
                'left': {'style': 'SOLID'}, 'right': {'style': 'SOLID'}
            }
        }
        ws.format(cell_range, cell_format)
        print(f"Successfully updated {len(rows)} rows to {SHEET_NAME}")
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")
# USER_NAME  = Pp.User() # 이제 GUI에서 사용자 이름이 직접 전달되므로 주석 처리 또는 제거
SOLD_TAG = "판매완료 or 삭제 / Sold out or Deleted"

HEYDEALER_ACCOUNTS = {
    "seobuk": "nTvLMmy29hC5#T9", # 실제 사용하는 ID와 비밀번호로 변경하세요.
    "inter77": "Seobuk2021**",
    "leeks21": "Dlrbtjd1366@"
}
HEYDEALER_LOGIN_URL = "https://dealer.heydealer.com/login"

try:
    gc = gspread.service_account(filename=Pp.Google_API()).open(FILE_NAME)
except Exception as e:
    print(f"Error connecting to Google Sheet: {e}")
    gc = None

def make_driver(headless=False):
    opts = webdriver.ChromeOptions()
    
    if headless:
        opts.add_argument("--headless=new")
    
    # 서버 환경을 위한 필수 옵션
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--remote-debugging-port=9222") # 포트 충돌 방지
    
    # 경로 설정 (Streamlit Cloud 리눅스 환경 표준 경로)
    opts.binary_location = "/usr/bin/chromium" 
    
    # 다운로드 경로 설정 (os 임포트 확인 필요)
    download_path = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    opts.add_experimental_option("prefs", {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    
    # Service 객체를 명시적으로 사용하여 실행
    from selenium.webdriver.chrome.service import Service
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=opts)

def one_line(s):
    # \r, \n, \t 포함 모든 연속 공백을 한 칸으로
    return re.sub(r'\s+', ' ', str(s or '').replace('\xa0',' ')).strip()

# =========================
# 유틸
# =========================
def safe_text(el):
    return el.text.strip() if el else ""

def try_find(driver, by, value, timeout=5):
    """
    WebDriverWait를 사용하여 특정 요소가 나타날 때까지 기다린 후 반환.
    타임아웃 시 None을 반환하여 프로그램 중단을 방지함.
    """
    try:
        # ✅ WebDriverWait를 사용하여 요소가 나타날 때까지 기다립니다.
        return Wait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        # TimeoutException 발생 시 None 반환
        return None
    except Exception as e:
        # 그 외 다른 오류 발생 시 None 반환
        print(f"Error in try_find: {e}")
        return None

def click_js(driver, el):
    driver.execute_script("arguments[0].click();", el)

def now_date():
    return time.strftime("%Y-%m-%d")

def read_existing_row_index():
    # 시트의 다음 입력 행 (헤더가 1행이라고 가정)
    try:
        ws = gc.worksheet(SHEET_NAME)
        return len(ws.get_all_values()) + 1
    except gspread.exceptions.WorksheetNotFound:
        # 시트가 없으면 새로 만들거나 첫 행으로 가정
        ws = gc.add_worksheet(SHEET_NAME, rows=1000, cols=40)
        return 2

# 1) 주소: 클릭 없이 li들 중 "주소처럼 보이는 줄"만 골라 선택
def get_encar_location(driver):
    import re
    # 방법 1: 속성값(판매자정보)을 기준으로 찾기 (가장 추천)
    li_xpath = "//*[contains(@data-impression, '판매자정보')]//ul/li"
    lis = driver.find_elements(By.XPATH, li_xpath)
    texts = [one_line(li.get_attribute("innerText") or li.text) for li in lis if one_line(li.get_attribute("innerText") or li.text)]
    # 만약 위 방법으로 안 잡힐 경우를 대비한 백업 (사진 속 클래스 직접 지정)
    if not lis:
        li_xpath = "//ul[@class='YtNR8dNHOS']/li"
        lis = driver.find_elements(By.XPATH, li_xpath)

    texts = [li.get_attribute("innerText").strip() for li in lis if li.text or li.get_attribute("innerText")]
    
    if not texts:
        return ""

    # 주소 판단에 방해되는 문구는 전부 제외
    BAN = (
        "종사원증", "종사원 증", "종사원증번호",
        "상사/조합정보", "상사/조합 정보",
        "사업자", "사업자번호",
        "판매중", "판매완료", "리뷰", "보증", "정보", "대표", "연락처", "CC21"
    )

    def looks_like_addr(t: str) -> bool:
        if any(b in t for b in BAN):
            return False
        has_lvl1 = any(x in t for x in ("시", "도"))
        has_lvl2 = any(x in t for x in ("구", "군", "동", "읍", "면"))
        has_road = any(x in t for x in ("로", "길", "번길", "대로"))
        # 예: "경남 창원시 마산회원구" (도로명 없이 시/구 조합)
        return (has_lvl1 and has_lvl2) or has_road

    # 1) ul의 3번째 li가 있으면 우선 주소 후보로 검사
    if len(texts) >= 3 and looks_like_addr(texts[2]):
        return texts[2]

    # 2) 뒤에서부터 주소처럼 보이는 줄을 찾기(주소가 보통 아래쪽)
    for t in reversed(texts):
        if looks_like_addr(t):
            return t

    # 3) 아주 마지막 백업: 점수 기반 선택(금지어/번호는 감점)
    def score(t: str) -> int:
        s = 0
        if any(x in t for x in ("시", "도")): s += 1
        if any(x in t for x in ("구", "군", "동", "읍", "면")): s += 1
        if any(x in t for x in ("로", "길", "번길", "대로")): s += 1
        if re.search(r"\d", t): s -= 1   # 번호 위주 줄은 감점
        if any(b in t for b in BAN): s -= 3
        return s

    return max(texts, key=score)

# 2) 주소+상호+이름 합치기
def get_encar_seller_line(driver):
    addr = get_encar_location(driver)
    
    # 판매자 정보 버튼 요소를 먼저 잡습니다.
    seller_btn = try_find(driver, By.XPATH, "//*[@data-enlog-dt-eventname='판매자정보']", timeout=1.0)
    
    company = ""
    name = ""
    
    if seller_btn:
        # 1. 이름(Name) 추출: strong 태그 (예: 박*철, 허대성)
        name_el = try_find(seller_btn, By.XPATH, ".//strong[not(contains(@class, 'blind'))]", timeout=0.5)
        name = one_line(name_el.get_attribute("innerText")) if name_el else ""
        
        # 2. 상호(Company) 추출: 모든 span 태그를 가져와서 합칩니다.
        # 사진 2처럼 span이 여러 개인 경우를 대비합니다.
        span_els = seller_btn.find_elements(By.TAG_NAME, "span")
        span_texts = [one_line(s.get_attribute("innerText")) for s in span_els if s.text or s.get_attribute("innerText")]
        
        if span_texts:
            # ["OK모터스", "매매"] -> "OK모터스 (매매)" 형태로 예쁘게 합치거나
            # 상사명만 중요시한다면 첫 번째 요소만 쓸 수도 있습니다.
            if len(span_texts) > 1:
                company = f"{span_texts[0]} ({span_texts[1]})" # 예: OK모터스 (매매)
            else:
                company = span_texts[0] # 예: 개인

    combined = " ".join([s for s in [addr, company, name] if s])
    return combined, addr, company, name

# 3) 직구(엔카믿고) 판별: 플로팅 버튼의 실제 표시 텍스트만 확인
def is_encar_direct_purchase(driver):
    for btn in driver.find_elements(By.XPATH, "//button[@data-enlog-dt-eventnamegroup='플로팅']"):
        try:
            if btn.is_displayed():
                label = (btn.get_attribute("innerText") or btn.text or "").strip()
                return "엔카를 통해 구매하기" in label
        except:
            continue
    return False

# =========================
# 전화버튼 헬퍼
# =========================
SAFE_PHONE_TEXTS = ("전화", "연락처", "문의")

def find_phone_button(driver):
    # 1차: 고정 위치 버튼
    b = try_find(driver, By.XPATH,
        '//*[@id="wrap"]/div/div[1]/div[1]/div[5]/div/div[1]/div[4]/button', timeout=1.2)
    if b and b.is_displayed():
        lab = (b.get_attribute("innerText") or b.text or "").strip()
        if any(k in lab for k in SAFE_PHONE_TEXTS) and "엔카를 통해 구매하기" not in lab:
            return b

    # 2차: 판매자 블록 내부 버튼(플로팅 제외)
    for b in driver.find_elements(By.XPATH, "//*[@id='detailSeller']//button"):
        try:
            if not b.is_displayed():
                continue
            lab = (b.get_attribute("innerText") or b.text or "").strip()
            if lab and "엔카를 통해 구매하기" not in lab and any(k in lab for k in SAFE_PHONE_TEXTS):
                return b
        except:
            continue
    return None

def get_phone_number_text_from_new_xpath(driver):
    """
    새로운 XPath에서 050으로 시작하는 전화번호 텍스트를 추출합니다.
    """
    PHONE_NUMBER_XPATH = '//*[@id="bottom_sheet"]/div[2]/div[2]/div/div[1]/p[2]'

    # try_find 함수가 요소를 찾아 반환한다고 가정
    phone_element = try_find(driver, By.XPATH, PHONE_NUMBER_XPATH, timeout=1.5)

    if phone_element and phone_element.is_displayed():
        # 요소의 텍스트를 가져옵니다.
        phone_text = (phone_element.text or phone_element.get_attribute("textContent") or "").strip()

        # 050으로 시작하는 번호인지 확인합니다.
        if phone_text.startswith("050") and phone_text:
            return phone_text
            
    return None

# =========================
# --- Encar: 판매완료/삭제 페이지 감지 ---
# =========================

def is_encar_sold_page(driver, timeout=2.5):
    """
    엔카 상세가 '판매되었거나 삭제된 차량' 안내 화면인지 판별.
    - p.DetailNone_text__* 존재 + 텍스트 확인
    - 또는 '동급 차량 보기' 버튼 존재
    로딩 타이밍을 고려해 짧게 폴링.
    """
    X_MSG = "//*[starts-with(@class,'DetailNone_text__')]"            # 안내문 단락
    X_ALT = "//button[normalize-space(.)='동급 차량 보기']"            # 대체 신호

    end = time.time() + timeout
    while time.time() < end:
        # 대체 신호 먼저 빠르게 체크
        alt = try_find(driver, By.XPATH, X_ALT, timeout=0.2)
        if alt:
            return True

        # 안내문 텍스트 체크 (pseudo 전처리 대비 innerText 우선)
        el = try_find(driver, By.XPATH, X_MSG, timeout=0.2)
        if el:
            txt = one_line(el.get_attribute("innerText") or el.text or "")
            if "판매되었거나 삭제된 차량" in txt:
                return True

        time.sleep(0.1)

    return False

#==================================================
# --- Encar 모델명 추출: 스팬 사이만 공백 ---
#==================================================

def get_encar_title(driver, timeout=3):
    """
    h3.DetailSummary_tit_car__* 안의 <span> 텍스트를 '스팬 사이만' 공백으로 이어 붙여 반환.
    - 스팬 내부 문자열은 가공하지 않음(엔카 표기 그대로 유지)
    - 스팬이 없을 때만 h3 전체 텍스트 사용
    - 공백 정리(연속 공백, NBSP)만 수행
    """
    X_H3 = '//div[@data-impression="기본정보"]//h3'
    

    try:
        # ✅ 먼저 부모 h3 태그가 DOM에 나타날 때까지 기다립니다.
        Wait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, X_H3)))
        
        # ✅ 이후 짧게 대기하여 h3 내부의 자식 요소들이 로드될 시간을 줍니다.
        time.sleep(0.5)

        # ✅ 이제 h3 태그를 찾고, 그 안의 모든 span을 안전하게 찾습니다.
        h3 = driver.find_element(By.XPATH, X_H3)
        spans = h3.find_elements(By.TAG_NAME, "span")
        
        parts = []
        for s in spans:
            text = (s.get_attribute("innerText") or s.text or "").strip()
            if text:
                parts.append(text)
        
        title = " ".join(parts).strip()
    except Exception:
        # 오류 발생 시 h3 전체 텍스트를 백업으로 사용
        h3_el = driver.find_element(By.XPATH, X_H3)
        title = (h3_el.get_attribute("innerText") or h3_el.text or "").strip() if h3_el else ""

    # 공백 정리
    title = title.replace("\xa0", " ")
    title = " ".join(title.split())

    return title

# =========================
# 사이트별 스크래퍼: 결과 dict 반환
# =========================

def scrape_encar(driver, url, row_idx_hint):
    """
    반환 dict 예시:
    {
      "site": "Encar",
      "link": <PC링크>,
      "date": YYYY-MM-DD,
      "year": "2020",
      "name_ko": "그랜저 하이브리드...",
      "fuel_ko": "가솔린",
      "engine": "2,400cc",
      "mileage": "86,000km",
      "plate": "12가3456",
      "color_ko": "검정색",
      "phone": "...",
      "location": "...",
      "price": 21500000*10000 (정수),
      "row": <엑셀 행번호>
    }
    """
    out = {
        "site": "Encar",
        "link": url,
        "date": now_date(),
        "year": "",
        "name_ko": "",
        "fuel_ko": "",
        "engine": "",
        "mileage": "",
        "plate": "",
        "color_ko": "",
        "phone": "",
        "location": "",
        "price": None,
        "row": row_idx_hint
    }
    # carId
    m = re.search(r'(\d{8})', url)
    if not m: return out
    carId = m.group(1)

    driver.get(f"https://fem.encar.com/cars/detail/{carId}?type=detail")
    out["link"] = driver.current_url

    # ↙↙ 판매완료/삭제 화면이면: 모델명에 태그 붙이고 카매니저 스킵되도록 plate 비워둔 채 조기 종료
    if is_encar_sold_page(driver):
        # 메시지 아래에 종종 모델명이 한 줄로 노출되는 경우가 있어, 있으면 가져오고 없으면 빈값
        base_name = ""
        try:
            alt = try_find(driver, By.XPATH, "//*[contains(text(),'동급 차량')]/preceding::p[1]", timeout=1)
            if alt:
                base_name = one_line(alt.get_attribute("innerText") or alt.text)
        except:
            pass

        out["name_ko"] = f"{base_name} · {SOLD_TAG}" if base_name else SOLD_TAG

        # 카매니저가 자동 스킵되도록 번호는 비워두고, 나머지는 최소값으로
        out.update({
            "encar_sold": True,
            "plate": "",            # ← plates 리스트에 안 들어가서 CM 스킵
            "phone": "-",
            "location": "-",
            "price": None
        })

        print(f"[ENCAR] Sold/deleted detected ({carId}) → name tagged & CM skip")
        return out
        
    # ① 직구 여부
    direct = is_encar_direct_purchase(driver)
    out["encar_direct"] = direct
    if direct:
        print(f"[ENCAR] Direct-purchase detected ({carId}) → seller/phone skip")
        out.update({
            "location": "엔카믿고서비스",
            "location_addr": "", "seller_company": "", "seller_name": "",
            "phone": "엔카믿고서비스"
        })
    else:
        # ② 주소/상호/이름
        out["location"], out["location_addr"], out["seller_company"], out["seller_name"] = get_encar_seller_line(driver)
        
        # ③ 전화 (3단계 클릭 로직 적용)
        
        phone_number = "엔카믿고서비스" # 기본값 설정

        try:
            # 1단계: 첫 번째 버튼(팝업 레이어 오픈) 찾기 및 클릭
            btn1_xpath = '//*[@id="wrap"]/div/div[1]/div[1]/div[5]/div/div[1]/div[4]/button'
            btn1 = try_find(driver, By.XPATH, btn1_xpath, timeout=2.0)
            
            if btn1 and btn1.is_displayed():
                # 버튼을 화면 중앙으로 스크롤하고 클릭 (안정성 확보)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn1)
                time.sleep(0.5)
                click_js(driver, btn1)
                print("[Encar Phone Step 1]: 첫 번째 버튼 클릭 성공 (팝업 오픈)")
                time.sleep(1.0) # 팝업이 로드될 시간 대기

                # 2단계: 팝업 레이어 안의 두 번째 버튼 (전화번호 보기) 찾기 및 클릭
                btn2_xpath = '//*[@id="bottom_sheet"]/div[2]/div[2]/div/div[2]/button[2]'
                btn2 = try_find(driver, By.XPATH, btn2_xpath, timeout=2.0)
                
                if btn2 and btn2.is_displayed():
                    click_js(driver, btn2)
                    print("[Encar Phone Step 2]: 두 번째 버튼 클릭 성공 (050 번호 노출 시도)")
                    time.sleep(1.5) # 번호가 노출될 시간 대기

                    # 3단계: 노출된 050- 전화번호 텍스트 추출
                    phone_txt_xpath = '//*[@id="bottom_sheet"]/div[2]/div[2]/div/div[1]/p[2]'
                    phone_el = try_find(driver, By.XPATH, phone_txt_xpath, timeout=1.0)
                    
                    if phone_el:
                        extracted_phone = (phone_el.text or phone_el.get_attribute("textContent") or "").strip()
                        if extracted_phone.startswith("050"):
                            phone_number = extracted_phone
                            print(f"[Encar 전화번호 추출 성공]: {phone_number}")
                        else:
                            print("[Encar Warning]: 텍스트를 찾았으나 050으로 시작하지 않음.")
                    else:
                        print("[Encar Warning]: 3단계: 전화번호 텍스트 요소 찾기 실패.")
                else:
                    print("[Encar Warning]: 2단계: 두 번째 버튼 찾기 실패.")
            else:
                print("[Encar Warning]: 1단계: 첫 번째 버튼 찾기 실패.")
                
        except Exception as e:
            print(f"[Encar Error] 전화번호 추출 중 예외 발생: {e}")

        # 추출된 번호를 out 딕셔너리에 저장 (실패 시 기본값 "엔카믿고서비스" 유지)
        out["phone"] = phone_number
    
    # ⑤ 모델명 추출 (이 부분이 누락되어 있었습니다!)
    try:
        # get_encar_title 함수를 호출하여 name_ko에 저장
        out["name_ko"] = get_encar_title(driver, timeout=4)
        print(f"[Encar 모델명]: {out['name_ko']}")
    except:
        out["name_ko"] = "모델명 미확인"
    
    # 가격 추출 (XPath 수정: 텍스트 기준)
    try:
        price_el = driver.find_element(By.XPATH, '//p[contains(., "만원")]/span[1]')
        ptxt = price_el.get_attribute("innerText").strip().replace(',', '')
        out["price"] = int(ptxt) * 10000
    except: out["price"] = None

    # 차량번호 추출 (XPath 수정: 사진 image_730de9 반영)
    try:
        plate_xpath = '//dt[contains(text(), "차량번호")]/following-sibling::dd'
        plate_el = Wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, plate_xpath)))
        out["plate"] = plate_el.get_attribute("innerText").strip()
        print(f"   [Plate 추출 성공]: {out['plate']}")
    except Exception as e:
        print(f"Error fetching Encar plate: {e}")
        out["plate"] = None

    # 상세 스펙 (자세히 버튼 및 idx_map 수정)
    try:
        # 버튼 찾기: 텍스트 기준
        detail_btn = Wait(driver, 2.5).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="자세히"]')))
        click_js(driver, detail_btn)
        time.sleep(1.5)

        # 팝업 내부 li 순서 기준 매핑 (image_72f384 반영)
        idx_map = {2:"year", 3:"mileage", 4:"engine", 5:"fuel_ko", 8:"color_ko"}
        for i, k in idx_map.items():
            # 팝업 내 ul > li[i] 안의 두 번째 span 또는 전체 텍스트
            xpath = f"(//div[contains(@class,'BottomSheet')]//ul/li)[{i}]/span"
            el = try_find(driver, By.XPATH, xpath, timeout=1.0)
            if not el: continue
            txt = el.get_attribute("innerText").strip()
            
            if k == "year":
                m2 = re.search(r'(\d{2})', txt)
                out["year"] = f"20{m2.group(1)}" if m2 else txt
            else:
                out[k] = txt
    except: pass

    return out

def scrape_seobuk(driver, url, row_idx_hint):
    out = {
        "site": "SEOBUK",
        "link": url, "date": now_date(),
        "year": "", "name_ko": "", "fuel_ko": "", "engine": "-", "mileage": "",
        "plate": "", "color_ko": "", "phone": "-", "location": "-", "price": None,
        "price_raw": None, "row": row_idx_hint,
    }

    # 1. URL에서 차량 ID 추출
    m = re.search(r'(\d{9})', url)
    if not m: return out
    carId = m.group(1)

    # 2. Headless 환경을 위해 창 크기 강제 설정 (요소가 숨겨지는 것 방지)
    driver.set_window_size(1920, 1080)

    # 3. 데이터 로딩 대기 로직 (최대 2회 시도)
    for attempt in range(2):
        try:
            driver.get(f"https://www.seobuk.org/search/detail/{carId}")
            
            # car-no가 나타날 때까지 대기
            wait = Wait(driver, 15) # 대기 시간을 15초로 늘림
            wait.until(EC.presence_of_element_located((By.ID, 'car-no')))
            
            # 번호가 비어있지 않은지 확인 (로딩 중엔 공백일 수 있음)
            time.sleep(2) 
            plate_text = safe_text(driver.find_element(By.ID, 'car-no'))
            
            if plate_text and len(plate_text) > 4:
                out["plate"] = plate_text
                break # 성공 시 루프 탈출
        except Exception as e:
            if attempt == 0:
                print(f"[SEOBUK] 1차 시도 실패, 재시도 중... ({carId})")
                driver.refresh()
                time.sleep(3)
            else:
                print(f"[SEOBUK] 최종 로딩 타임아웃: {carId}")
                return out

    # 4. 데이터 추출 (더 견고한 Selector 사용)
    try:
        # 모델명 추출
        name_el = try_find(driver, By.CSS_SELECTOR, '.car-title-box p', timeout=3)
        if name_el:
            out["name_ko"] = safe_text(name_el).split(']')[-1].strip()

        # 가격 추출
        price_el = try_find(driver, By.CSS_SELECTOR, '.representativeColor', timeout=3)
        if price_el:
            digits = re.sub(r'[^\d]', '', safe_text(price_el))
            if digits: out["price_raw"] = int(digits)

        # 상세 표 정보 (연식, 연료, 주행거리 등)
        # XPath 대신 표의 텍스트 구조를 이용해 데이터 매칭
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
        for row in rows:
            th_text = safe_text(try_find(row, By.TAG_NAME, "th"))
            td_text = safe_text(try_find(row, By.TAG_NAME, "td"))
            if "연식" in th_text: out["year"] = td_text
            elif "연료" in th_text: out["fuel_ko"] = td_text
            elif "주행거리" in th_text: out["mileage"] = td_text
            elif "색상" in th_text: out["color_ko"] = td_text
    except Exception as e:
        print(f"[SEOBUK] 필드 추출 중 오류: {e}")

    return out

def scrape_kb(driver, url, row_idx_hint):
    out = {
        "site": "KB",
        "link": url,
        "date": now_date(),
        "year": "",
        "name_ko": "",
        "fuel_ko": "",
        "engine": "",
        "mileage": "",
        "plate": "",
        "color_ko": "",
        "phone": "",
        "location": "",
        "price": None,
        "row": row_idx_hint
    }
    m = re.search(r'(\d{8})', url)
    if not m:
        return out
    carId = m.group(1)

    # 모바일 페이지 → 팝업 닫고 수집
    driver.get(f"https://m.kbchachacha.com/public/web/car/detail.kbc?carSeq={carId}&homeServiceCarYn=N")
    out["link"] = driver.current_url

    # 팝업 닫기
    try:
        Wait(driver, 2.5).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '괜찮아요, 모바일 웹으로 볼게요')]")))
        popup_btn = driver.find_element(By.XPATH, "//*[contains(text(), '괜찮아요, 모바일 웹으로 볼게요')]")
        click_js(driver, popup_btn)
        time.sleep(0.8)
    except TimeoutException:
        pass

    # plate
    raw_plate_el = try_find(driver, By.CLASS_NAME, "header-txt-link")
    if raw_plate_el:
        out["plate"] = raw_plate_el.text.replace(" 복사", "").strip()

    # 차명
    el_name = try_find(driver, By.CSS_SELECTOR, 'h2.car-intro__name')
    out["name_ko"] = safe_text(el_name)

    # 기본정보 탭 클릭
    try:
        info_btn = Wait(driver, 2.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabBtnCarInfo"]/ul/li[2]/button')))
        click_js(driver, info_btn)
        time.sleep(1.0)
    except:
        pass

    # 연식
    try:
        year_text = driver.find_element(By.XPATH, '//dt[normalize-space(text())="연식"]/following-sibling::dd').text
        yy = re.search(r'(\d{2})년', year_text)
        out["year"] = f"20{yy.group(1)}" if yy else year_text
    except:
        pass

    # 주행거리
    try:
        out["mileage"] = driver.find_element(By.XPATH, '//dt[normalize-space(text())="주행거리"]/following-sibling::dd').text
    except:
        pass

    # 연료
    try:
        out["fuel_ko"] = driver.find_element(By.XPATH, '//dt[normalize-space(text())="연료"]/following-sibling::dd').text.strip()
    except:
        pass

    # 가격
    try:
        price_text = driver.find_element(By.CSS_SELECTOR, 'span.car-intro__cost-highlight > strong').text
        out["price"] = int(price_text.replace(',', '')) * 10000
    except:
        out["price"] = None

    # 배기량
    try:
        out["engine"] = driver.find_element(By.XPATH, '//dt[normalize-space(text())="배기량"]/following-sibling::dd').text.strip()
    except:
        pass

    # 색상
    try:
        out["color_ko"] = driver.find_element(By.XPATH, '//dt[normalize-space(text())="차량 색상"]/following-sibling::dd').text.strip()
    except:
        pass

    # 딜러홈 → 전화/지역 파싱
    try:
        dealer_btn = Wait(driver, 2.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="btnDealerHome1"]/span')))
        click_js(driver, dealer_btn)
        time.sleep(1.2)
        html = driver.page_source
        m_phone = re.search(r'var safeTel = \"(\d+?)\"', html)
        if m_phone:
            digits = m_phone.group(1)
            out["phone"] = f'{digits[:4]}-{digits[4:8]}-{digits[8:]}' if len(digits) == 12 else digits
        m_loc = re.search(r'var addr = "(.+?)"', html)
        if m_loc:
            out["location"] = m_loc.group(1)
    except:
        pass

    # PC 링크로 변환(선호 시)
    out["link"] = f'https://www.kbchachacha.com/public/car/detail.kbc?carSeq={carId}'
    return out

# 파일의 적절한 위치에 추가 (예: scrape_kb 함수 다음)

def heydealer_login(driver, login_id: str, login_pw: str):
    """
    헤이딜러 딜러 페이지에 로그인하는 함수.
    """
    driver.get(HEYDEALER_LOGIN_URL)

    X_ID_INPUT = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div/form/div[1]/div/div/div/div[1]/input'
    
    # 제공된 PW XPath는 불완전합니다. ID와 유사한 구조를 가정하여 입력 필드(input)로 재구성합니다.
    # 일반적으로 PW 필드는 div[2] 아래에 위치합니다.
    X_PW_INPUT = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div/form/div[2]/div/div/div/div[1]/input'
    
    # 로그인 버튼 XPath (텍스트 기반 검색으로 안정화)
    X_LOGIN_BTN = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div/form/button[2]/div/div[1]'
    
    X_SUCCESS_ELEMENT = '//*[@id="root"]/div[2]/div[1]/div/div/div[2]/a/h5'
    try:
        # 1. ID 입력
        id_input = Wait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, X_ID_INPUT))
        )
        id_input.send_keys(login_id)
        
        # 2. PW 입력
        pw_input = try_find(driver, By.XPATH, X_PW_INPUT, timeout=5)
        if not pw_input:
            print("[HEYDEALER] Warning: PW input field not found.")
            return False
        pw_input.send_keys(login_pw)
        
        # 3. 로그인 버튼 클릭
        login_btn = Wait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, X_LOGIN_BTN))
        )
        click_js(driver, login_btn) 
        
        # 4. 로그인 성공 확인 (가장 중요한 대기 조건)
        
        # 4-A: 로그인 버튼이 사라질 때까지 잠시 대기
        # 이 단계는 로그인 처리 중임을 확인하는 보조적인 단계입니다.
        try:
            Wait(driver, 5).until(
                EC.invisibility_of_element_located((By.XPATH, X_LOGIN_BTN))
            )
        except TimeoutException:
            # 버튼이 사라지지 않아도 다음 단계로 진행하여 최종 요소를 확인합니다.
            pass
        
        # 4-B: 메인 페이지의 고유 요소가 나타날 때까지 최대 15초를 기다립니다.
        Wait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, X_SUCCESS_ELEMENT))
        )
        
        print(f"[HEYDEALER] Login successful for ID: {login_id}. Main page element found.")
        return True
        
    except TimeoutException:
        print(f"[HEYDEALER] Login attempt failed for ID {login_id}: Timeout while waiting for successful login (Success element not found).")
        return False
    except Exception as e:
        print(f"[HEYDEALER] Login failed for ID {login_id} (General Error): {e}")
        return False

# 참고: GUI에서 선택된 ID를 인수로 받는 최종 함수는 run_pipeline 내부에서 구현됩니다.
# 기존 scrape_heydealer 함수를 아래 코드로 대체합니다.

# 기존 scrape_heydealer 함수를 아래 코드로 대체합니다.

def scrape_heydealer(driver, url, row_idx_hint):
    out = {
        "site": "HEYDEALER", # 1. site를 "HEYDEALER"로 고정
        "link": url,
        "date": now_date(),
        "year": "",
        "name_ko": "",
        "fuel_ko": "",       # <--- 여기에 연료 정보 저장
        "engine": "-", 
        "mileage": "",       
        "plate": "",         
        "color_ko": "",      
        "cm_dealer": "-",        
        "location": "-",     
        "price": None,       
        "row": row_idx_hint,
        "delivery_schedule": "",
        "hd_vehicle_price": None, 
        "hd_account": "-",
        }
    
    carId = None
    
    # 1. URL에서 고유 ID 추출 (다양한 패턴 대응)
    m_dealer = re.search(r'/cars/([a-zA-Z0-9]{8})', url)
    if m_dealer:
        carId = m_dealer.group(1)
    
    m_mobile = re.search(r'(HD\d+)', url)
    if m_mobile:
        carId = m_mobile.group(1)

    if not carId:
        print(f"[HEYDEALER] Could not extract car ID from URL: {url}")
        return out
        
    # 2. 웹 페이지 접속 및 스크래핑

    # 딜러 링크 형태의 URL일 경우
    if m_dealer:
        driver.get(url) 
        out["link"] = driver.current_url
        time.sleep(2.5)
        print(f"[HEYDEALER] Accessed dealer URL: {out['link']}")
    
        # 딜러 페이지에서 필요한 정보 추출 시도
        
        # 1. 연료 (Fuel) - 사용자 요청 XPath 적용
        try:
            fuel_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/span[1]', timeout=3)
            out["fuel_ko"] = safe_text(fuel_el)
            print(f"[HEYDEALER 연료]: {out.get('fuel_ko', '추출 실패')}")
        except:
            print("[HEYDEALER] Warning: Failed to parse fuel.")
            pass            
           
        # 3. 전화번호 (Phone) - 이전 요청 XPath 적용
        try:
            phone_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[2]/div/div/div[4]/div[2]/div[2]', timeout=3)
            out["cm_dealer"] = safe_text(phone_el)
            print(f"[HEYDEALER 전화번호]: {out.get('cm_dealer', '추출 실패 또는 없음')}")
        except:
            pass
            
        # 4. 가격 (Price) - 이전 요청 XPath 적용
        try:
            price_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div[1]/div[1]/div/div[3]/h5', timeout=3)
            price_text = safe_text(price_el).replace('만원', '').replace(',', '').strip()
            if price_text.isdigit():
                out["price"] = int(price_text) * 10000
            else:
                out["price"] = None
            print(f"[HEYDEALER 가격]: {out.get('price', '추출 실패 또는 없음')}")
        except:
            pass
            
        # 5. 색상 (Color) - 이전 요청 XPath 적용
        try:
            color_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/span[4]', timeout=3)
            out["color_ko"] = safe_text(color_el)
            print(f"[HEYDEALER 색상]: {out.get('color_ko', '추출 실패')}")
        except:
            pass
            
        # 6. 지역 (Location) - 이전 요청 XPath 적용
        try:
            location_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[3]', timeout=3)
            out["location"] = safe_text(location_el)
            print(f"[HEYDEALER 지역]: {out.get('location', '추출 실패')}")
        except:
            pass
            
        # 7. 주행거리 (Mileage) - 이전 요청 XPath 적용
        try:
            mileage_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]', timeout=3)
            out["mileage"] = safe_text(mileage_el)
            print(f"[HEYDEALER 주행거리]: {out.get('mileage', '추출 실패')}")
        except:
            pass
            
        # 8. 번호판 (Plate) - 이전 요청 XPath 적용
        try:
            plate_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/p', timeout=3)
            out["plate"] = safe_text(plate_el)
            print(f"[HEYDEALER 번호판]: {out.get('plate', '추출 실패')}")
        except:
            pass 
            
        # 9. 차명/연식 - 이전 요청 XPath 적용
        try:
            name_el = try_find(driver, By.XPATH, '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/h1', timeout=3)
            
            full_title = safe_text(name_el)
            title_no_plate = re.sub(r'\(.+?\)\s*', '', full_title).strip()
            
            year_match = re.search(r'(\d{4})년식', title_no_plate)
            if year_match:
                out["year"] = year_match.group(1)

            name_only = re.sub(r'^\d{4}년식\s*', '', title_no_plate).strip()
            out["name_ko"] = one_line(name_only)
            
            print(f"[HEYDEALER 차명]: {out.get('name_ko', '추출 실패')}")
        except:
            print("[HEYDEALER] Warning: Failed to parse title/year from dealer page.")
            pass

        try:
            YEAR_XPATH = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/span[2]'
            year_el = try_find(driver, By.XPATH, YEAR_XPATH, timeout=3)
            
            if year_el:
                year_text = safe_text(year_el) # 예: "17년형"
                
                # 텍스트에서 숫자만 추출합니다.
                year_digits = re.search(r'(\d+)', year_text)
                
                if year_digits:
                    two_digits_year = year_digits.group(1) # 예: "17"
                    
                    # 2자리 연도를 4자리로 변환 (20XX 가정)
                    if len(two_digits_year) == 2:
                        out["year"] = f"20{two_digits_year}" # 예: "2017"
                    else:
                        out["year"] = two_digits_year
                    
                    print(f"[HEYDEALER 연식 추출 성공]: {out['year']}")
                else:
                    print("[HEYDEALER] Warning: 연식 텍스트에서 숫자를 찾지 못했습니다.")
        
        

        except Exception as e:
            print(f"[HEYDEALER] Error: 연식 추출 중 오류 발생: {e}")
            pass
            
        # 10. (기존 로직 유지) 연료 외 나머지 스펙은 XPath로 대체되었거나 해당 사항 없음

    # 10. 계좌번호 (Account Number) - Index 19 (T열)
        try:
            # XPATH: //*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[2]/div/section/div[1]/div[3]/div[2]
            account_xpath = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[2]/div/section/div[1]/div[3]/div[2]'
            account_el = try_find(driver, By.XPATH, account_xpath, timeout=3)
            out["hd_account"] = safe_text(account_el)
            print(f"[HEYDEALER 계좌번호]: {out.get('hd_account', '추출 실패 또는 없음')}")
        except:
            print("[HEYDEALER] Warning: Failed to parse account number.")
            out["hd_account"] = "-"
            pass 
            
        # 11. 차량금액 (Vehicle Price) - Index 23 (X열)
        try:
            # XPATH: //*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[2]/div/section/div[1]/div[2]/div[2]
            price_xpath = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[2]/div/section/div[1]/div[2]/div[2]'
            price_el = try_find(driver, By.XPATH, price_xpath, timeout=3)
            price_text = safe_text(price_el) # 예: "950만원"

            # ✅ 수정된 로직: "만원" 제거 및 쉼표/숫자 외 문자 제거 후 10000 곱하기
            # '950만원' -> '950'
            digits_text = re.sub(r'[^\d]', '', price_text.replace('만원', '').strip())
            
            if digits_text:
                # '950' -> 950 * 10000 = 9500000
                out["hd_vehicle_price"] = int(digits_text) * 10000
            else:
                out["hd_vehicle_price"] = None

            print(f"[HEYDEALER 차량금액]: {out.get('hd_vehicle_price', '추출 실패 또는 없음')}")
        except Exception as e:
            print(f"[HEYDEALER] Warning: Failed to parse vehicle price. Error: {e}")
            out["hd_vehicle_price"] = None
            pass

        # ===================================================================
        # ✅ STEP 2: 추가 정보 화면을 위한 버튼 클릭 및 로딩 대기
        # ===================================================================
        try:
            click_button_xpath = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[1]/button[2]'
            click_el = try_find(driver, By.XPATH, click_button_xpath, timeout=3)
            
            if click_el:
                # 1. 화면 중앙으로 스크롤 (안정성 강화)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", click_el)
                time.sleep(0.5) 
                
                # 2. ✅ JS 강제 클릭으로 'element click intercepted' 우회
                click_js(driver, click_el) 
                print("[HEYDEALER] JS Clicked button to reveal additional info.")
                
                # 화면 변경 대기
                wait_for_xpath = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[2]/form/div[1]/section[1]/h3'
                Wait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, wait_for_xpath))
                )
                print("[HEYDEALER] Additional info section loaded.")

            else:
                print("[HEYDEALER] Warning: Click button for additional info not found.")
        except TimeoutException:
            print("[HEYDEALER] Error: Click button or target section timed out.")
            pass
        except Exception as e:
            # 이 오류를 잡기 위해 메시지를 출력합니다.
            print(f"[HEYDEALER] Error during click/wait for additional info: {e}") 
            pass
        # ===================================================================
        
        # 12. 탁송일정 (Delivery Schedule) - Index 11 (L열) (클릭 후)
        try:
            # XPATH: //*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[2]/form/div[1]/section[1]/div[2]/div[1]/div/span
            schedule_xpath = '//*[@id="root"]/div[2]/div[2]/div[1]/div[1]/div[4]/div[2]/form/div[1]/section[1]/div[2]/div[1]/div/span'
            schedule_el = try_find(driver, By.XPATH, schedule_xpath, timeout=3)
            out["delivery_schedule"] = safe_text(schedule_el) 
            print(f"[HEYDEALER 탁송일정]: {out.get('delivery_schedule', '추출 성공')}")
        except:
            print("[HEYDEALER] Warning: Failed to parse delivery schedule.")
            pass
        
    # 모바일 판매 링크 형태의 URL일 경우 (기존 로직 유지)
    elif m_mobile:
        driver.get(f"https://m.heydealer.com/sell/detail/{carId}")
        out["link"] = driver.current_url
        time.sleep(2.0)
        print(f"[HEYDEALER] Accessed mobile URL: {out['link']}")

        # 모바일 파싱 로직 (기존 유지)
        try:
            title_el = try_find(driver, By.CSS_SELECTOR, 'p.css-15h2e0u', timeout=3)
            title_text = safe_text(title_el)
            year_match = re.search(r'^(\d{4})년식', title_text)
            if year_match: out["year"] = year_match.group(1)
            name_only = re.sub(r'^\d{4}년식\s*', '', title_text).strip()
            out["name_ko"] = one_line(name_only)
            
            plate_el = try_find(driver, By.CSS_SELECTOR, 'p.css-t0n3j7', timeout=1)
            out["plate"] = safe_text(plate_el)

            spec_list = driver.find_elements(By.CSS_SELECTOR, 'div.css-1k947f6')
            for spec in spec_list:
                label = safe_text(spec.find_element(By.CSS_SELECTOR, 'p.css-17s27o9')) 
                value = safe_text(spec.find_element(By.CSS_SELECTOR, 'p.css-4m6b5r')) 
                
                if "주행거리" in label: out["mileage"] = value
                elif "연료" in label: out["fuel_ko"] = value
                elif "색상" in label: out["color_ko"] = value
            
        except Exception as e:
            print(f"[HEYDEALER] Warning: Mobile spec parsing error: {e}")

    # 3. 최종 링크 정리
    if not m_dealer:
        out["link"] = f'https://www.heydealer.com/sell/detail/{carId}' 
    
    return out

# =========================
# 카매니저: 로그인 1회 + 여러 plate 처리
# =========================

def crawl_carmanager_many(driver, plates, login_id='seobuk77', login_pw='Bg5MAWjNGnaktBg'):
    """
    반환: dict[plate] = {"dealer": str, "location": str, "price": int}
    """
    result = {}
    driver.get('http://www.carmanager.co.kr/')

    # 로그인(있으면 스킵)
    try:
        user_inp = try_find(driver, By.NAME, "userid", timeout=4)
        if user_inp:
            user_inp.send_keys(login_id)
            driver.find_element(By.NAME, "userpwd").send_keys(login_pw)
            driver.find_element(By.XPATH, '//*[@id="ui_loginarea"]/tbody/tr/td[2]/button').click()
            time.sleep(0.8)
    except:
        pass

    # 팝업 닫기
    try:
        btn = try_find(driver, By.ID, 'cmapppopupclose_OnClick', timeout=3)
        if btn: click_js(driver, btn)
    except:
        pass

    # “매물조회” 진입
    try:
        Wait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="gnb"]/li[2]/a'))).click()
    except Exception as e:
        print(f"[CM] 매물조회 진입 실패: {e}")
        return result

    # 지역 고정(서울) 1~2회 시도
    for _ in range(2):
        try:
            time.sleep(2.5)
            click_js(driver, Wait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ui_searchsido"]/li[2]/div/button/div'))))
            time.sleep(0.5)
            click_js(driver, Wait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ui_searchsido"]/li[2]/div/div/ul/li[1]/label/input'))))
            time.sleep(0.5)
        except:
            pass

    # Plate 루프
    for plate in plates:
        try:
            # 요소들(입력/버튼)은 매 plate마다 새로 취득
            inp  = Wait(driver, 3).until(EC.element_to_be_clickable((By.NAME, 'tbxSearchCarNumber')))
            btn  = Wait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search"]/div/div[4]/table/tbody/tr/td[2]/button')))

            # tbody는 갱신 감지 위해 항상 fresh로 가져옴
            def get_tbody():
                return Wait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ui_context"]/table/tbody')))

            tbody = get_tbody()
            before = tbody.get_attribute('innerHTML')

            # 검색 실행
            inp.clear()
            inp.send_keys(plate)
            btn.click()

            # 변화 감지 (최대 1.2초)
            deadline = time.time() + 1.2
            while time.time() < deadline:
                try:
                    tbody_now = get_tbody()  # stale 방지: 항상 재획득
                    cur = tbody_now.get_attribute('innerHTML')
                    if cur != before:
                        tbody = tbody_now
                        break
                except StaleElementReferenceException:
                    # 잠깐 쉬고 다시 시도
                    time.sleep(0.05)
                time.sleep(0.05)

            # 결과 2번째 행(tr[2]) 없으면 '미조회'
            try:
                row2 = tbody.find_element(By.XPATH, './tr[2]')
            except Exception:
                result[plate] = {"dealer": "", "location": "", "price": 0}
                continue

            # 안전 파서 (timeout 짧게)
            def quick_text(xp, t=0.8):
                try:
                    el = Wait(driver, t).until(EC.presence_of_element_located((By.XPATH, xp)))
                    return one_line(el.get_attribute('innerText') or el.text or '')
                except Exception:
                    return ''

            dealer  = quick_text('//*[@id="ui_context"]/table/tbody/tr[2]/td[12]/span[2]')
            loc     = quick_text('//*[@id="ui_context"]/table/tbody/tr[2]/td[11]')
            price_s = quick_text('//*[@id="ui_context"]/table/tbody/tr[2]/td[10]//b')

            try:
                price = int(price_s.replace(',', '')) * 10000 if price_s else 0
            except Exception:
                price = 0

            result[plate] = {"dealer": dealer, "location": loc, "price": price}

        except StaleElementReferenceException:
            # 한번 더 아주 짧게 재시도(완전 동일 로직 반복은 무거우니 즉시 미조회 처리)
            print(f"[CM] {plate} stale once → mark as not found")
            result[plate] = {"dealer": "", "location": "", "price": 0}
        except Exception as e:
            print(f"[CM] {plate} 처리 중 오류: {e}")
            result[plate] = {"dealer":"", "location":"", "price":0}
    
    return result

def scrape_autowini(driver, url, row_idx_hint):
    """
    Autowini 사이트에 로그인하여 Car ID로 검색하고 첫 차량의 모델명만 추출합니다.
    - 상세 페이지 접근 및 추가 정보 추출은 생략합니다.
    """
    out = {
        "site": "AUTOWINI",
        "link": url,
        "date": now_date(),
        "year": "-",
        "name_ko": "MODEL NAME FAILED", # 추출 실패 시 쉽게 식별 가능하도록 기본값 설정
        "fuel_ko": "-",
        "engine": "-",
        "mileage": "-",
        "plate": "",             # 카매니저 스킵
        "color_ko": "-",
        "phone": "-",
        "location": "해외수출",    
        "price": "-",
        "price_raw": None,       
        "row": row_idx_hint,
    }

    # 1. Car ID 추출 
    m = re.search(r'([A-Z]{2}\d{7})', url) 
    if not m:
        print("Error: Autowini Car ID not found in URL.")
        return out
    carId = m.group(1)
    print(f"Autowini Car ID: {carId}")

    # 2. 업데이트된 로그인 수행
    LOGIN_URL = "https://www.autowini.com/joinfree/login"
    driver.get(LOGIN_URL)
    
    try:
        # ID/PW 입력 필드 및 로그인 버튼 대기
        id_input = Wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="username"]')))
        
        # ✅ XPATH 오타 수정된 버전 사용
        pw_input = Wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
        
        login_btn = Wait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="frmLogin"]/div[1]/a')))
        
        id_input.send_keys('nnann')
        pw_input.send_keys('gustn1174')
        
        click_js(driver, login_btn)
        
        # ✅ 로그인 후 페이지 이동 전 랜덤 딜레이
        login_delay = random.uniform(1.5, 3.5)
        print(f"  > Delay after login: {login_delay:.2f}s")
        time.sleep(login_delay) 
        print("Autowini login attempted.")
        
        # 로그인 후 메인 페이지로 이동 (검색을 위해)
        driver.get("https://www.autowini.com/")
        time.sleep(1.0)

    except Exception as e:
        print(f"Autowini login failed: {e}")
        # 로그인 실패 시 계속 진행 (검색 실패 가능성 높음)

    # 3. Car ID로 사이트 내부 검색 및 이름 추출
    try:
        # 1. Car ID 입력 필드가 나타날 때까지 기다립니다.
        search_input_xpath = '//*[@id="i_skeyword_Search"]'
        
        search_input = Wait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, search_input_xpath)))
        search_input.clear()
        search_input.send_keys(carId)
        
        # ✅ URL 입력 후 엔터를 누르기 전 랜덤 딜레이
        delay_search = random.uniform(1.0, 2.0)
        print(f"  > Delay before search ENTER: {delay_search:.2f}s")
        time.sleep(delay_search) 
        
        # 2. ENTER 키를 보내 검색을 실행합니다.
        search_input.send_keys(Keys.ENTER) 
        print("Sent ENTER key to initiate search.")
        
        # 3. 검색 결과 로딩 대기
        time.sleep(5.0) 
        
        # 4. 검색 결과의 첫 번째 차량 이름 추출
        # XPATH: //*[@id="root"]/div/main/section/div[3]/a/div[2]/div/p[1]/span
        name_xpath = '//*[@id="root"]/div/main/section/div[3]/a/div[2]/div/p[1]/span'
        name_el = try_find(driver, By.XPATH, name_xpath, timeout=5)
        
        if name_el:
            out["name_ko"] = safe_text(name_el)
            out["link"] = driver.current_url # 현재 검색 결과 페이지 URL을 저장
        else:
            print("Warning: Model name element not found after search.")
            out["name_ko"] = f"SEARCH FAILED: {carId}"

    except Exception as e:
        print(f"🚨 Autowini 검색 또는 이름 추출 중 오류 발생: {e}")
        out["name_ko"] = f"EXCEPTION: {carId}"
            
    return out

# =========================
# 시트 쓰기(배치)
# =========================

def to_sheet_rows(records, start_row, user_name, seq_start=1):
    """
    기존 포맷 유지 + A열은 고정 번호(1..n)로 기록.
    수식에 필요한 실제 시트 행번호는 r 그대로 사용.
    """
    rows = []
    r = start_row
    for i, rec in enumerate(records, start=0):
        seq = seq_start + i  # ✅ A열에 들어갈 1,2,3,...

        site = rec["site"]
        link = rec["link"]
        buyer = rec.get("buyer","")
        year = rec.get("year","")
        name_ko = rec.get("name_ko","")
        fuel_ko = rec.get("fuel_ko","")
        engine = rec.get("engine","-")
        mileage = rec.get("mileage","")
        plate = rec.get("plate","")
        color_ko = rec.get("color_ko","")
        phone = rec.get("phone","-")
        location = rec.get("location","-")
        price = rec.get("price", None)

        dealer_no = rec.get("cm_dealer","")
        cm_loc    = rec.get("cm_location","")
        cm_price  = rec.get("cm_price",0)
        delivery_schedule = rec.get("delivery_schedule", "") 
        hd_account = rec.get("hd_account", "-")
        hd_vehicle_price = rec.get("hd_vehicle_price", None)

        hd_id_for_sheet = rec.get("hd_login_id", "N/A")

        # ✅ T열 (Index 19): 계좌번호(HD) / CM 딜러(기타)
        t_column_val = hd_account if site == "HEYDEALER" else cm_loc
        
        # ✅ W열 (Index 22): 차량금액(HD) / N/A(기타)
        w_column_val = hd_vehicle_price if site == "HEYDEALER" and hd_vehicle_price is not None else "N/A"

        row = [
            seq,                     # ✅ A열: 고정 번호(1..n)
            link,                    # B
            user_name,               # C (주석은 시트 구조에 맞춰 조정하세요)
            hd_id_for_sheet,                   # D
            now_date(),              # E
            year,                    # F
            f'=googletranslate("{name_ko}","ko","en")' if name_ko else "",
            f'=googletranslate("{fuel_ko}","ko","en")' if fuel_ko else "",
            engine,
            mileage,
            plate,
            "",
            delivery_schedule if site == "HEYDEALER" else "-", # M (Index 12),
            f'=googletranslate("{color_ko}","ko","en")' if color_ko else "",
            site,
            phone,
            location,
            price if price is not None else "-",
            dealer_no,
            t_column_val,
            cm_price,
            "N/A",       # [₩] 운송비
            w_column_val,       # [₩] 계산서O
            "N/A",       # [₩] 계산서X
            "N/A",       # [₩] 매도비
            f'=W{r}+X{r}+Y{r}',                # [₩] 총금액(차량대)
            f'=((W{r}+Y{r})*0.915)+X{r}+V{r}', # [₩] NET COST
            f'=AA{r}/$AG$1',                   # [$] USD 판매원가
            "N/A" if site != "SEOBUK" else (rec.get("price_raw","-") or "-"),
            f'=AC{r}-AB{r}',                   # [$] PROFIT
            f'=R{r}/$AH$1',                    # [$] USD ENCAR
            f'=AC{r}-AE{r}',                   # [$] USD Encar - Selling Price
            buyer,                             
        ]
        rows.append(row)
        r += 1

    return rows

# =========================
# 수정된 run_pipeline 함수
# =========================
def run_pipeline(list_pairs, user_name, headless=True, hd_login_id=None):
    """
    1) 소스별 크롤링 → records 메모리 저장
    2) plate 모아 carmanager를 1회 로그인 후 대량 조회
    3) cm 결과를 records에 병합
    4) 시트에 배치 기록 (SEOBUK PROJECTION / NUEVO PROJECTION#2)
    """
    if gm.get_nuevo_projection_sheet() is None:
        st.error("구글 시트 연결에 실패했습니다. 설정을 확인하세요.")
        return

    # 1. 초기화 및 알림
    st.info(f"🚀 {user_name} 님, 크롤링을 시작합니다. (대상: {len(list_pairs)}건)")
    driver = make_driver(headless=headless)
    
    records = []
    plates = []
    hd_logged_in = False
    
    # 시작 행 결정 (NUEVO PROJECTION#2 시트 기준)
    try:
        ws = gm.get_nuevo_projection_sheet()
        all_vals = ws.get_all_values()
        start_row = len(all_vals) + 1
        st.write(f"📊 현재 시트 데이터: {len(all_vals)}행 (기록 시작 위치: {start_row}행)")
    except Exception as e:
        st.error(f"시트 정보를 가져오지 못했습니다: {e}")
        driver.quit()
        return

    # A단계: 소스별 스크래핑 루프
    for idx, (url, buyer) in enumerate(list_pairs, start=1):
        row_hint = start_row + len(records)
        url = url.strip()
        buyer = buyer.strip()
        
        st.write(f"---")
        st.write(f"🔄 ({idx}/{len(list_pairs)}) 수집 중: {url[:50]}...")
        
        rec = None
        skip_cm = False

        try:
            # 사이트별 분기 로직 (기존 로직 유지)
            if "encar" in url:
                rec = scrape_encar(driver, url, row_hint)
            elif "seobuk" in url:
                rec = scrape_seobuk(driver, url, row_hint)
            elif "kbchachacha" in url:
                rec = scrape_kb(driver, url, row_hint)
            elif "autowini" in url.lower():
                rec = scrape_autowini(driver, url, row_hint)
            elif "heydealer" in url:
                # 헤이딜러 로그인 처리 (최초 1회)
                if not hd_logged_in and hd_login_id:
                    hd_login_pw = HEYDEALER_ACCOUNTS.get(hd_login_id)
                    st.write(f"🔑 헤이딜러 로그인 시도 중 ({hd_login_id})...")
                    if heydealer_login(driver, hd_login_id, hd_login_pw):
                        hd_logged_in = True
                        st.write("✅ 헤이딜러 로그인 성공")
                
                if hd_logged_in:
                    rec = scrape_heydealer(driver, url, row_hint)
                    if rec: rec["hd_login_id"] = hd_login_id
                else:
                    st.warning("⚠️ 헤이딜러 로그인이 되지 않아 스킵합니다.")
                    continue
                
                skip_cm = True # 헤이딜러는 카매니저 조회 제외

            # 결과 처리
            if rec:
                rec["buyer"] = buyer
                rec["user"] = user_name
                records.append(rec)
                st.write(f"✅ 수집 성공: {rec.get('name_ko', '차명 미확인')}")
                
                # 카매니저 조회를 위해 번호판 수집
                if rec.get("plate") and not skip_cm:
                    plates.append(rec["plate"])
            else:
                st.warning(f"⚠️ {url} 에서 데이터를 가져오지 못했습니다.")

        except Exception as e:
            st.error(f"❌ 처리 중 상세 오류 발생: {e}")
            continue

    # B단계: 카매니저 통합 조회 (로그인 1회 후 여러 plate 처리)
    if plates:
        unique_plates = list(dict.fromkeys(plates))
        st.write(f"🔎 카매니저 정보 조회 시작 ({len(unique_plates)}대)...")
        try:
            cm_map = crawl_carmanager_many(driver, unique_plates)
            
            # C단계: 수집된 records에 카매니저 결과 병합
            for rec in records:
                if not rec.get("cm_skip") and rec.get("plate"):
                    p = rec["plate"]
                    cm = cm_map.get(p, {})
                    rec["cm_dealer"]   = cm.get("dealer", "")
                    rec["cm_location"] = cm.get("location", "")
                    rec["cm_price"]    = cm.get("price", 0)
            st.write("✅ 카매니저 정보 매핑 완료")
        except Exception as e:
            st.error(f"카매니저 조회 중 오류 발생: {e}")

    # D단계: 구글 시트 배치 업데이트
    if records:
        st.write(f"📝 시트에 데이터 기록 중... (대상: {len(records)}건)")
        try:
            # 데이터 행 변환
            rows = to_sheet_rows(records, start_row, user_name)
            # 시트 전송 (gm 모듈 사용)
            flush_to_sheet(rows, start_row)
            st.success(f"🎊 모든 작업이 완료되었습니다! {len(records)}건이 시트에 반영되었습니다.")
        except Exception as e:
            st.error(f"시트 기록 중 오류 발생: {e}")
    else:
        st.warning("⚠️ 수집된 데이터가 없어 시트를 업데이트하지 않았습니다.")

    driver.quit()
