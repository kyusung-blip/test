import streamlit as st
from projection import execute_crawling  # projection.py에서 크롤링 함수 임포트
import traceback
import logging
from urllib.parse import urlparse

# Configure logging only if not already configured
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 페이지 설정
st.set_page_config(page_title="프로젝션 관리", layout="wide")

# 세션 상태 초기화
if "progress_logs" not in st.session_state:
    st.session_state["progress_logs"] = []  # 진행 상태 로그 저장
if "waiting_list" not in st.session_state:
    st.session_state["waiting_list"] = []  # 대기 중 작업 리스트
if "in_progress" not in st.session_state:
    st.session_state["in_progress"] = []  # 진행 중 작업 리스트
if "completed_list" not in st.session_state:
    st.session_state["completed_list"] = []  # 완료된 작업 리스트

# Google Sheets와 관련된 설정
def load_secrets(account_type):
    """Streamlit Secrets에서 선택된 GCP 계정을 로드"""
    try:
        secrets_data = st.secrets[account_type]
        logging.info(f"[load_secrets] {account_type} 로드 성공")
        return secrets_data
    except KeyError:
        logging.error(f"[load_secrets] {account_type}에 대한 정보가 없습니다")
        st.error(f"[{account_type}]에 대한 정보가 없습니다.")
        return None

# GCP Service Account 선택
account_type = st.sidebar.selectbox(
    "GCP Service Account 선택", ["gcp_service_account_seobuk", "gcp_service_account_concise"]
)
secrets = load_secrets(account_type)  # secrets 로드
if secrets:
    spreadsheet_names = secrets["spreadsheet_name"]
    selected_sheet = st.sidebar.selectbox("스프레드시트를 선택하세요", spreadsheet_names)

# 상단 UI 구성
st.markdown("### Sales팀: 프로젝션 관리")
sales_team = st.selectbox("🚀 Sales팀 선택", ["JINSU", "MINJI", "ANGEL", "OSW", "CORAL", "JEFF", "VIKTOR"])
url = st.text_input("🌐 URL 입력", placeholder="예: https://example.com")
buyer = st.text_input("🛒 Buyer 이름 입력", placeholder="예: John Doe")

if st.button("저장"):
    # Validate inputs before saving
    errors = []
    
    if not url:
        errors.append("URL을 입력해주세요")
    else:
        # Proper URL validation
        url_clean = url.strip()
        try:
            parsed_url = urlparse(url_clean)
            if not parsed_url.scheme or not parsed_url.netloc:
                errors.append("유효한 URL 형식이 아닙니다 (도메인이 없거나 프로토콜이 누락됨)")
            elif parsed_url.scheme not in ("http", "https"):
                errors.append("URL은 http:// 또는 https://로 시작해야 합니다")
        except Exception as e:
            errors.append(f"URL 파싱 오류: {str(e)}")
    
    if not buyer:
        errors.append("Buyer 이름을 입력해주세요")
    elif not buyer.strip():
        errors.append("Buyer 이름은 공백만으로 구성될 수 없습니다")
    
    if errors:
        for error in errors:
            st.error(f"❌ {error}")
    else:
        # Trim whitespace
        url_clean = url.strip()
        buyer_clean = buyer.strip()
        
        st.session_state["waiting_list"].append({
            "sales_team": sales_team,
            "url": url_clean,
            "buyer": buyer_clean
        })
        st.success(f"✅ 대기 중 리스트에 저장 완료: Buyer={buyer_clean}, URL={url_clean}")

# 작업 리스트 및 진행 상태
st.markdown("### 작업 리스트")
tab1, tab2, tab3 = st.tabs(["⏳ 대기 중", "🚀 진행 중", "✅ 완료"])  # 탭 생성

# 대기 중 작업 탭
with tab1:
    st.write("📋 대기 중 작업 리스트")
    if not st.session_state["waiting_list"]:
        st.info("현재 대기 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["waiting_list"]):
            st.write(f"{idx + 1}. Sales팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
            if st.button(f"작업 실행: {idx + 1}", key=f"start_{idx}"):
                # Validate secrets before execution
                if not secrets:
                    st.error("❌ GCP 인증 정보가 없습니다. 왼쪽 사이드바에서 계정을 선택해주세요.")
                    logging.error("[UI] GCP 인증 정보 없음")
                    continue
                
                if not selected_sheet:
                    st.error("❌ 스프레드시트가 선택되지 않았습니다.")
                    logging.error("[UI] 스프레드시트 선택되지 않음")
                    continue
                
                with st.spinner(f"🔄 {item['buyer']} 작업 실행 중..."):
                    try:
                        logging.info(f"[UI] 작업 실행 시작 - Sales팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
                        print(f"[UI] 작업 실행 시작 - Sales팀: {item['sales_team']}, URL: {item['url']}, Buyer: {item['buyer']}")
                        completed_task = execute_crawling(
                            [item],  # 대기 작업
                            secrets,  # GCP 인증 정보
                            selected_sheet  # 스프레드시트 이름
                        )
                        logging.info(f"[UI] execute_crawling 반환값: {completed_task}")
                        print(f"[UI] execute_crawling 반환값: {completed_task}")

                        if completed_task and len(completed_task) > 0:
                            # Process each record
                            success_count = 0
                            failed_count = 0
                            
                            for record in completed_task:
                                if record.get("status") == "FAILED":
                                    failed_count += 1
                                    error_detail = record.get('error', 'Unknown Error')
                                    st.error(f"❌ {record.get('buyer', 'N/A')} 작업 실패: {error_detail}")
                                    logging.error(f"[UI] 작업 실패 - Buyer: {record.get('buyer')}, Error: {error_detail}")
                                    print(f"[UI] 작업 실패 - Buyer: {record.get('buyer')}, Error: {error_detail}")
                                else:
                                    success_count += 1
                                    st.success(f"✅ {record.get('buyer', 'N/A')} 작업 완료! 차량명: {record.get('car_name', 'N/A')}")
                                    logging.info(f"[UI] 작업 성공 - Buyer: {record.get('buyer')}, 차량명: {record.get('car_name')}")
                                    print(f"[UI] 작업 성공 - Buyer: {record.get('buyer')}, 차량명: {record.get('car_name')}")
                            
                            # Summary message
                            st.info(f"📊 처리 결과: 성공 {success_count}건, 실패 {failed_count}건")
                        else:
                            error_msg = "작업 실패: 반환 값이 없습니다. 로그를 확인하세요."
                            st.error(f"❌ {item['buyer']} {error_msg}")
                            logging.error(f"[UI] {error_msg}")
                            print(f"[UI] {error_msg}")
                    except Exception as e:
                        error_msg = f"작업 실행 중 예외 발생: {str(e)}"
                        st.error(f"❌ {error_msg}")
                        logging.error(f"[UI ERROR] {error_msg}")
                        logging.error(traceback.format_exc())
                        print(f"[UI ERROR] {error_msg}")
                        print(traceback.format_exc())

# 진행 중 작업 탭
with tab2:
    st.write("📋 진행 중 작업")
    if not st.session_state["in_progress"]:
        st.info("현재 진행 중인 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["in_progress"]):
            st.write(f"작업 중: {item['buyer']}")

# 완료된 작업 탭
with tab3:
    st.write("📋 완료된 작업")
    if not st.session_state["completed_list"]:
        st.info("완료된 작업이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state["completed_list"]):
            st.write(f"{idx + 1}. 완료됨: {item['buyer']}")

# 로그 출력
st.markdown("### 작업 로그")
if st.session_state["progress_logs"]:
    for log in st.session_state["progress_logs"]:
        st.write(log)
else:
    st.info("현재 작업 로그가 없습니다.")
