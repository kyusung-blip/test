import streamlit as st
import requests
import pandas as pd

# Streamlit 세션 상태 초기화 (저장된 데이터를 유지)
if "saved_data" not in st.session_state:
    st.session_state["saved_data"] = []

# Streamlit UI (입력 섹션)
st.title("Crawling Task Manager")

with st.form("input_form"):
    sales_team = st.text_input("Enter Sales Team Name")       # 세일즈 팀 이름
    url = st.text_area("Enter URLs (One URL per line)")       # URL (여러개 입력 가능)
    buyer = st.text_input("Enter Buyer Name")                # 바이어 이름
    submitted = st.form_submit_button("Save Task")           # 저장 버튼

    if submitted:
        # URL을 새 줄 단위로 처리하여 저장
        urls = [u.strip() for u in url.split("\n") if u.strip()]
        for u in urls:
            st.session_state["saved_data"].append(
                {"sales_team": sales_team, "url": u, "buyer": buyer}
            )
        st.success("Task saved!")

# 저장된 데이터 표시
if st.session_state["saved_data"]:
    st.write("### Saved Tasks")
    st.dataframe(pd.DataFrame(st.session_state["saved_data"]))

# Flask 서버로 작업 요청 전송
if st.button("Start Crawling"):
    try:
        # Server로 POST 요청 전송
        data = st.session_state["saved_data"]
        if not data:
            st.warning("No tasks to send. Please save a task first.")
        else:
            response = requests.post(
                "http://192.168.0.38:5000/start-tasks", json=data
            )  # Flask 서버로 요청
            if response.status_code == 200:
                st.success("Crawling tasks started successfully!")
            else:
                st.error(f"Failed to start tasks. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error: Could not connect to server. {e}")

# 작업 상태 확인
if st.button("Check Status"):
    try:
        response = requests.get("http://192.168.0.38:5000/status")  # 상태 확인 요청
        if response.status_code == 200:
            status_data = response.json()
            tasks = status_data.get("tasks", [])
            if tasks:
                # 진행 중 작업
                in_progress = [t for t in tasks if t["status"] == "running"]
                # 완료된 작업
                completed = [t for t in tasks if t["status"] == "completed"]

                st.write("### In-progress Tasks")
                if in_progress:
                    st.dataframe(pd.DataFrame(in_progress))
                else:
                    st.info("No tasks in progress.")

                st.write("### Completed Tasks")
                if completed:
                    st.dataframe(pd.DataFrame(completed))
                else:
                    st.info("No tasks completed yet.")

                # 프로그레스 바
                st.progress(len(completed) / len(tasks))
            else:
                st.info("No tasks found.")
        else:
            st.error(f"Failed to fetch status. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching status: {e}")
