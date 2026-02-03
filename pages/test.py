import streamlit as st
import requests

st.title("Flask Server Connection Test")

if st.button("Check Connection"):
    try:
        # Flask 서버의 엔드포인트에 요청
        response = requests.get("http://localhost:5000/ping", timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.success(f"Connection successful: {data['message']}")
        else:
            st.error(f"Server responded with status code: {response.status_code}")
    except Exception as e:
        st.error(f"Could not connect to server: {e}")
