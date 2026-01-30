import streamlit as st
from auth import get_google_sheet
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

# --- 크롤러 로직 ---
def make_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("window-size=1920x1080")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(options=options)

def crawl_encar(driver, url):
    driver.get(url)
    try:
        name = Wait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3.DetailSummary_tit_car__"))).text
        price_element = driver.find_element(By.CLASS_NAME, "DetailLeadCase_point__vdG4b")
        price = int(price_element.text.replace(",", "").replace("만원", "")) * 10000
        return {"name": name, "price": price}
    except TimeoutException:
        return {"name": "Error", "price": 0}
    finally:
        driver.quit()

# --- Streamlit UI ---
st.title("🚗 크롤링 시스템")

# 상단 입력
sales_person = st.selectbox("👤 Sales 팀원 선택", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"])
url = st.text_input("🌐 URL 입력", placeholder="크롤링할 차량 URL을 입력하세요")
if st.button("크롤링 시작"):
    with st.spinner("크롤링 중..."):
        driver = make_driver(headless=True)
        result = crawl_encar(driver, url)
        st.success(f"크롤링 성공! 차량 이름: {result['name']}, 가격: {result['price']}원")

# 하단 작업 관리
st.header("📋 저장된 작업")
sheet = get_google_sheet("Inventory SEOBUK", "2026")
tasks = sheet.get_all_records()
if tasks:
    for task in tasks:
        st.write(task)
else:
    st.write("저장된 작업이 없습니다.")
