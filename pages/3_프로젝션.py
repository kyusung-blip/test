import streamlit as st
import requests
import pandas as pd
import time

# (1) Streamlit UI: 세일즈팀/URL/바이어명 입력 및 저장
st.title("Crawling Task Manager")

# 저장 상태 유지 (입력 데이터 저장을 위한 초기화)
if "saved_data" not in st.session_state:
    st.session_state["saved_data"] = []

# 입력받은 값을 저장
with st.form("input_form"):
    sales_team = st.text_input("Enter Sales Team Name")
    url = st.text_area("Enter URLs (One URL per line)")
    buyer = st.text_input("Enter Buyer Name")
    submitted = st.form_submit_button("Save Task")
    
    if submitted:
        # URL을 개별 라인 단위로 추출
        urls = [u.strip() for u in url.split("\n") if u.strip()]
        for u in urls:
            st.session_state["saved_data"].append({"sales_team": sales_team, "url": u, "buyer": buyer})
        st.success("Saved!")

# 저장 데이터 표시
if st.session_state["saved_data"]:
    st.write("### Saved Tasks")
    st.dataframe(pd.DataFrame(st.session_state["saved_data"]))

# (2) 외부 파이썬 코드에 데이터 전달
if st.button("Start Crawling"):
    task_data = st.session_state["saved_data"]
    try:
        # 요청 보내기
        response = requests.post(
            "http://<external-server-ip>:5000/start-tasks",
            json=task_data
        )
        if response.status_code == 200:
            st.success("Crawling tasks started successfully!")
        else:
            st.error("Failed to start tasks.")
    except Exception as e:
        st.error(f"Error: Could not connect to server. {e}")

# (3) 작업 상태 확인
if st.button("Check Status"):
    try:
        response = requests.get("http://<external-server-ip>:5000/status")
        if response.status_code == 200:
            status_data = response.json()
            if status_data.get("tasks"):
                in_progress = [t for t in status_data["tasks"] if t["status"] == "running"]
                completed = [t for t in status_data["tasks"] if t["status"] == "completed"]
                
                st.write("### In-progress Tasks")
                st.dataframe(pd.DataFrame(in_progress))
                
                st.write("### Completed Tasks")
                st.dataframe(pd.DataFrame(completed))
                
                st.progress(len(completed) / len(status_data["tasks"]))
        else:
            st.error("Failed to fetch status.")
    except Exception as e:
        st.error(f"Error: Unable to fetch status. {e}")

# (4) 완료된 데이터 뷰
if st.button("View Completed"):
    try:
        response = requests.get("http://<external-server-ip>:5000/completed")
        if response.status_code == 200:
            completed_data = response.json()
            st.write("### Completed Data")
            st.dataframe(pd.DataFrame(completed_data))
        else:
            st.error("Failed to fetch completed data.")
    except Exception as e:
        st.error(f"Error: Unable to fetch completed data. {e}")
