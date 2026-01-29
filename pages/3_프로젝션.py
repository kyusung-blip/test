import streamlit as st

# 페이지 설정
st.set_page_config(page_title="프로젝션 관리", layout="wide")

# --- 상태 ���리 초기화 ---
if "progress_logs" not in st.session_state:
    st.session_state["progress_logs"] = []  # 진행 상태의 로그 저장
if "waiting_list" not in st.session_state:
    st.session_state["waiting_list"] = []  # 대기 중 리스트
if "in_progress" not in st.session_state:
    st.session_state["in_progress"] = []  # 진행 중 리스트
if "completed_list" not in st.session_state:
    st.session_state["completed_list"] = []  # 완료된 리스트

# --- 상단 구성: 드롭다운 / URL / buyer / 저장 버튼 ---
st.markdown("### Sales팀: 프로젝션 관리")
with st.container():  # 상단 비율 10%
    col1, col2, col3, col4 = st.columns([2, 6, 2, 2])  # 적절한 비율로 나눔

    sales_team = st.selectbox("🚀 Sales팀 선택", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"], key="selected_sales")
    url = st.text_input("🌐 URL 입력", placeholder="예: https://example.com")
    buyer = st.text_input("🛒 Buyer 이름 입력", placeholder="예: John Doe")
    
    if st.button("저장"):
        if url and buyer:
            st.session_state["waiting_list"].append({"sales_team": sales_team, "url": url, "buyer": buyer})
            st.success(f"✅ 대기 중 리스트에 저장 완료: {buyer} - {url}")
        else:
            st.error("❌ URL과 Buyer 이름을 모두 입력해주세요!")

# --- 중단 구성: 진행 상태 모니터링 ---
st.markdown("### 진행 상태")
with st.container():  # 중단 비율 10%
    if len(st.session_state["progress_logs"]) > 0:
        for log in st.session_state["progress_logs"]:
            st.info(f"🔄 {log}")
    else:
        st.write("현재 진행 상태가 없습니다.")

# --- 하단 구성: 텝으로 대기중 / 진행중 / 완료 나누기 ---
st.markdown("### 작업 리스트")
tab1, tab2, tab3 = st.tabs(["⏳ 대기 중", "🚀 진행 중", "✅ 완료"])

# --- 대기중 텝 ---
with tab1:
    st.write("📋 대기 중 리스트")
    if len(st.session_state["waiting_list"]) == 0:
        st.write("대기 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["waiting_list"]):
            st.write(f"{idx + 1}. 팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
            if st.button(f"작업 시작 {idx + 1}", key=f"start_{idx}"):
                st.session_state["in_progress"].append(item)
                del st.session_state["waiting_list"][idx]
                st.session_state["progress_logs"].append(f"🔄 {item['buyer']} 작업 시작됨")

# --- 진행중 텝 ---
with tab2:
    st.write("📋 진행 중 리스트")
    if len(st.session_state["in_progress"]) == 0:
        st.write("현재 진행 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["in_progress"]):
            st.write(f"{idx + 1}. 팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
            if st.button(f"작업 완료 {idx + 1}", key=f"complete_{idx}"):
                st.session_state["completed_list"].append(item)
                del st.session_state["in_progress"][idx]
                st.session_state["progress_logs"].append(f"✅ {item['buyer']} 작업 완료됨")

# --- 완료 텝 ---
with tab3:
    st.write("📋 완료된 리스트")
    if len(st.session_state["completed_list"]) == 0:
        st.write("완료된 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["completed_list"]):
            st.write(f"{idx + 1}. 팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
