import requests
import streamlit as st

st.title("Connection Test")

if st.button("Check Connection"):
    try:
        response = requests.get("http://localhost:5000/ping", timeout=10)
        st.write(response.text)
    except Exception as e:
        st.error(f"Connection failed: {e}")
