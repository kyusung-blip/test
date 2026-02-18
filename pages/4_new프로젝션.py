import streamlit as st
import crawling_queue_manager as cqm
import time

st.set_page_config(page_title="New 크롤링 시스템", layout="wide")

# 세션 초기화
if "crawling_active" not in st.session_state:
    st.session_state.crawling_active = False

st.title("🕷️ New 크롤링 시스템")
st.caption("실시간 공유 큐 기반 크롤링 - by SEOBUK")

# ===== 사이드바: 작업 입력 =====
with st.sidebar:
    st.header("📝 새 작업 추가")
    
    user_list = ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"]
    selected_user = st.selectbox("매입사원", user_list)
    
    hd_ids = ["seobuk", "inter77", "leeks21"]
    selected_hd_id = st.selectbox("헤이딜러 ID", hd_ids)
    
    links_input = st.text_area("Links (한 줄에 하나씩)", height=150, placeholder="https://...")
    buyers_input = st.text_area("Buyers (한 줄에 하나씩)", height=150, placeholder="John\nMike\n...")
    
    if st.button("💾 저장 및 큐에 추가", type="primary", use_container_width=True):
        links = [l.strip() for l in links_input.splitlines() if l.strip()]
        buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
        
        if not links or not buyers:
            st.error("링크와 바이어를 모두 입력해주세요.")
        elif len(links) != len(buyers):
            st.error("링크와 바이어 개수가 일치하지 않습니다.")
        else:
            with st.spinner("큐에 추가 중..."):
                count = cqm.add_tasks(selected_user, selected_hd_id, links, buyers)
                st.success(f"✅ {count}개 작업이 큐에 추가되었습니다!")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    
    # 크롤링 시작/중지 버튼
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 시작", use_container_width=True):
            # 시작 전 진행중 상태로 멈춘 작업 자동 초기화
            reset_count = cqm.reset_stuck_tasks()
            if reset_count > 0:
                st.info(f"🔄 {reset_count}건의 멈춘 작업을 초기화했습니다.")
                time.sleep(1)
            
            st.session_state.crawling_active = True
            st.rerun()
    
    with col2:
        if st.button("⏸️ 중지", use_container_width=True):
            st.session_state.crawling_active = False
            st.rerun()
    
    with col3:
        if st.button("🔁 실패 재시도", use_container_width=True):
            retry_count = cqm.retry_failed_tasks()
            if retry_count > 0:
                st.success(f"✅ {retry_count}건을 재시도 대기열에 추가했습니다.")
                time.sleep(1)
                st.rerun()
            else:
                st.info("재시도할 실패 작업이 없습니다.")

# ===== 메인: 탭 UI =====
tab1, tab2 = st.tabs(["📋 진행중/대기중", "✅ 완료"])

with tab1:
    st.subheader("📋 진행 상황")
    
    # 진행중 작업
    running = cqm.get_running_tasks()
    if running:
        st.markdown("### 🟢 진행중")
        for task in running:
            with st.container(border=True):
                st.markdown(f"**NO.{task['no']}** | {task['user']} | {task['hd_id']}")
                st.caption(f"🔗 Link: {task['link'][:50]}...")
                st.caption(f"👤 Buyer: {task['buyer']}")
                st.caption(f"⏰ 시작: {task['started_at']}")
    
    # 대기중 작업
    pending = cqm.get_pending_tasks()
    if pending:
        st.markdown(f"### 🟡 대기중 ({len(pending)}건)")
        for task in pending[:5]:  # 최대 5개만 표시
            with st.container(border=True):
                st.markdown(f"**NO.{task['no']}** | {task['user']} | {task['hd_id']}")
                st.caption(f"🔗 {task['link'][:50]}...")
                st.caption(f"👤 {task['buyer']}")
        
        if len(pending) > 5:
            st.info(f"+ 외 {len(pending) - 5}건 대기중")
    
    if not running and not pending:
        st.info("현재 진행 중이거나 대기 중인 작업이 없습니다.")

with tab2:
    st.subheader("✅ 완료된 작업")
    
    completed = cqm.get_completed_tasks()
    
    if completed:
        st.markdown(f"**총 {len(completed)}건 완료**")
        
        for task in completed[-10:]:  # 최근 10개만 표시
            status_icon = "✅" if task['status'] == "완료" else "❌"
            with st.container(border=True):
                st.markdown(f"{status_icon} **NO.{task['no']}** | {task['user']} | {task['hd_id']}")
                st.caption(f"🔗 {task['link'][:50]}...")
                st.caption(f"👤 {task['buyer']}")
                st.caption(f"⏰ 완료: {task['completed_at']}")
                if task['result']:
                    st.caption(f"📄 {task['result']}")
    else:
        st.info("완료된 작업이 없습니다.")

# ===== 자동 크롤링 로직 =====
if st.session_state.crawling_active:
    status_placeholder = st.empty()
    
    while st.session_state.crawling_active:
        pending = cqm.get_pending_tasks()
        
        if not pending:
            status_placeholder.success("✅ 모든 작업이 완료되었습니다. 크롤링을 중지합니다.")
            st.session_state.crawling_active = False
            time.sleep(2)
            st.rerun()
            break
        
        status_placeholder.info(f"🔄 크롤링 진행 중... (대기: {len(pending)}건)")
        
        result = cqm.run_next_task()
        
        status_placeholder.write(result["message"])
        time.sleep(2)
        st.rerun()
