import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 1. 연결 설정 (Streamlit의 Secrets 기능을 사용하도록 설계)
def get_gspread_client():
    # 보안을 위해 파일 대신 Streamlit 서버에 저장된 비밀 정보를 읽어옵니다.
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # st.secrets["gcp_service_account"]는 나중에 웹 설정에서 넣어줄 값입니다.
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

st.title("🔗 구글 시트 연결 테스트")

try:
    client = get_gspread_client()
    
    # 2. 테스트할 시트 열기 (기존에 쓰시던 시트 이름 중 하나)
    #에 정의된 "Dealer Information" 시트를 예시로 사용합니다.
    spreadsheet = client.open("Dealer Information")
    sheet = spreadsheet.sheet1
    
    # 3. 데이터 가져오기 테스트
    first_val = sheet.acell('A1').value
    
    st.success("✅ 구글 시트 연결에 성공했습니다!")
    st.write(f"**'Dealer Information' 시트의 A1 셀 내용:** {first_val}")

except Exception as e:
    st.error("❌ 연결에 실패했습니다.")
    st.exception(e)