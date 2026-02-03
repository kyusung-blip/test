import streamlit as st
import requests

# 제목 표시
st.title("Flask Server Connection Test")

# 연결 확인 버튼
if st.button("Check Connection"):
    try:
        # Flask 서버의 /ping 엔드포인트에 GET 요청
        response = requests.get("http://192.168.0.38:5000/ping")
        if response.status_code == 200:
            data = response.json()
            st.success(f"Connection successful: {data['message']}")
        else:
            st.error(f"Server responded with status code: {response.status_code}")
    except Exception as e:
        st.error(f"Could not connect to server: {e}")
