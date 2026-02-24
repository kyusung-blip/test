import streamlit as st
import re

def parse_car_info(raw_text):
    # 정규표현식: 17자리의 대문자+숫자 조합(VIN)을 찾습니다.
    # VIN은 보통 I, O, Q를 제외한 17자리 문자열입니다.
    vin_pattern = r'([A-Z0-9]{17})'
    
    lines = raw_text.strip().split('\n')
    results = []
    
    for line in lines:
        if not line.strip():
            continue
            
        # 1. VIN 찾기
        match = re.search(vin_pattern, line)
        if match:
            vin = match.group(1)
            vin_index = match.start()
            vin_end_index = match.end()
            
            # 2. VIN 앞부분은 '차명'
            car_name = line[:vin_index].strip()
            
            # 3. VIN 뒷부분 처리 (차량번호 + 색상)
            # 보통 차량번호는 '숫자2~3자리 + 한글1자리 + 숫자4자리' 형식입니다.
            remainder = line[vin_end_index:].strip()
            plate_pattern = r'(\d{2,3}[가-힣]\d{4})'
            plate_match = re.search(plate_pattern, remainder)
            
            if plate_match:
                # 차량번호 뒷부분이 색상
                color = remainder[plate_match.end():].strip()
            else:
                # 차량번호 패턴이 없을 경우 남은 부분을 색상으로 간주
                color = remainder
                
            # VIN 뒷 8자리 추출
            vin_8 = vin[-8:]
            results.append(f"{car_name} {vin_8} {color}")
            
    return results

# --- 스트림릿 화면 구성 ---
st.set_page_config(page_title="DK 배차 리스트 변환기", page_icon="🚚")

st.title("🚚 배차 리스트 변환기")
st.markdown("---")

# 1. 입력 칸 (Control + V)
input_data = st.text_area("정보를 아래에 붙여넣으세요:", height=200, placeholder="EVOQUESALVA2BN5GH13764256버0428BLUE...")

# 출발/도착지 설정 (사용자 수정 가능)
col1, col2 = st.columns(2)
with col1:
    departure = st.text_input("출발지", "서북")
with col2:
    arrival = st.text_input("도착지", "인천항")

if st.button("배차 리스트 생성하기"):
    if input_data:
        parsed_list = parse_car_info(input_data)
        count = len(parsed_list)
        
        # 2. 출력 칸 구성
        st.subheader("✅ 결과 확인")
        
        # 결과 텍스트 생성
        output_text = f"[{departure} -> {arrival}]\n\n"
        output_text += f"{count}대 배차 리스트 드립니다!!\n\n"
        
        for i, item in enumerate(parsed_list, 1):
            output_text += f"{i}. {item}\n"
            
        # 화면에 텍스트 영역으로 출력 (복사하기 편하게)
        st.text_area("아래 내용을 복사해서 사용하세요:", value=output_text, height=250)
        st.success("변환 완료!")
    else:
        st.warning("내용을 입력해주세요.")
