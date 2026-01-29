import streamlit as st

# 페이지 설정
st.set_page_config(page_title="탁송 관리", layout="wide")

# 페이지 콘텐츠
st.title("🚛 탁송 정보 생성기")
st.info("매입 프로그램에서 생성된 정보를 붙여넣고 출발지를 입력하면 탁송 기사용 메시지가 생성됩니다.")

# 1. 입력 영역
col1, col2 = st.columns([1, 1])
with col1:
    input_text = st.text_area("📋 매입 정보 붙여넣기", height=250, placeholder="차번호: ...\n주소: ...\n번호: ...")
    from_value = st.text_input("📍 출발지역 입력", placeholder="예: 수원, 장한평")

# 2. 공통 로직 함수
def process_tak_message(type_label, notice_text):
    if not input_text:
        st.error("매입 정보를 먼저 입력해주세요.")
        return
    
    route_line = f"{from_value} -> 서��"
    dispatch_line = "배차 후 바로 딜러와 통화해주세요"
    arrival_line = "도착 : 인천 연수구 능허대로 36 카택물류센터 SEOBUK 010-8399-8082"

    extracted_lines = []
    start_collecting = False
    
    # 기존 정규식 기반 대신 라인별 추출 로직 유지
    for line in input_text.splitlines():
        if line.startswith("사업자번호:"):
            continue
        if line.startswith("차번호:"):
            start_collecting = True
        if start_collecting:
            extracted_lines.append(line)
            if line.startswith("번호:"):
                break
    
    result = f"{route_line}\n{notice_text}\n\n" + "\n".join(extracted_lines) + f"\n\n{dispatch_line}\n\n{arrival_line}"
    return result

# 3. 버튼 및 출력 영역
with col2:
    st.subheader("🛠️ 출력 형식 선택")
    b_col1, b_col2, b_col3 = st.columns(3)
    
    result_msg = ""
    with b_col1:
        if st.button("일반", use_container_width=True):
            result_msg = process_tak_message("일반", "★서류 사무실에서 먼저 수령 후 차량 출고해주세요★")
    with b_col2:
        if st.button("서류/차량주소", use_container_width=True):
            result_msg = process_tak_message("주소분리", "★차량 주소에서 차량 픽업 후 서류주소에서 서류 받아야합니다!★")
    with b_col3:
        if st.button("차량내", use_container_width=True):
            result_msg = process_tak_message("차량내", "★서류 차량안에 있습니다.★")

    if result_msg:
        st.subheader("📝 생성된 탁송 메시지")
        st.code(result_msg, language="text")
        st.caption("위 박스 우측 상단의 아이콘을 클릭하면 복사됩니다.")
