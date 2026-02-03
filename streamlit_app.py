import streamlit as st
from auth import get_gspread_client_seobuk, get_gspread_client_concise

st.title("Multiple Google Service Accounts Example")

# 첫 번째 서비스 계정 사용 (Seobuk Project)
st.header("Seobuk Project Server")
try:
    gc_seobuk = get_gspread_client_seobuk()
    spreadsheet_seobuk = gc_seobuk.open("SEOBUK PROJECTION")  # 스프레드시트 이름
    worksheet_seobuk = spreadsheet_seobuk.worksheet("NUEVO PROJECTION#2")  # 워크시트 이름
    data_seobuk = worksheet_seobuk.get_all_records()
    st.write(data_seobuk)
except Exception as e:
    st.error(f"Error with Seobuk Project Server: {e}")

# 두 번째 서비스 계정 사용 (Concise Project)
st.header("Concise Project Server")
try:
    gc_concise = get_gspread_client_concise()
    spreadsheet_concise = gc_concise.open("SEOBUK PROJECTION")  # 스프레드시트 이름
    worksheet_concise = spreadsheet_concise.worksheet("NUEVO PROJECTION#2")  # 워크시트 이름
    data_concise = worksheet_concise.get_all_records()
    st.write(data_concise)
except Exception as e:
    st.error(f"Error with Concise Project Server: {e}")
