import streamlit as st
import requests

st.title("Flask Server Connection Test")

if st.button("Check Connection"):
    try:
        # Flask 서버의 엔드포인트가 정확한지 확인
        url = "http://localhost:5000/ping"
        st.write(f"Attempting to connect to {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.success(f"Connection successful: {data['message']}")
        else:
            st.error(f"Server responded with status code: {response.status_code}")
    except requests.ConnectionError as e:
        st.error(f"Connection error: {e}")
    except requests.Timeout as e:
        st.error(f"Request timed out: {e}")
    except Exception as e:
        st.error(f"An unknown error occurred: {e}")
