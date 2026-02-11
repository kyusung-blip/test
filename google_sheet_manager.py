import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@st.cache_resource
def get_spreadsheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    json_file = "concise-isotope-456307-n5-8cf3eb97b093.json"
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    gc = gspread.authorize(creds)
    return gc.open("Dealer Information")

def get_dealer_sheet():
    return get_spreadsheet().sheet1

def get_company_sheet():
    return get_spreadsheet().worksheet("상사정보")
