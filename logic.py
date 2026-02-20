# logic.py
import re
from mapping import VINYEAR_map, COLOR_map, ADDRESS_REGION_MAP
import brand

def parse_excel_data(raw_text):
    """탭으로 구분된 텍스트를 파싱하여 딕셔너리로 반환"""
    if not raw_text or not raw_text.strip():
        return {}

    parts = raw_text.split('\t')
    
    # 데이터 추출 (인덱스 기준)
    data = {
        "site": parts[1] if len(parts) > 1 else "",
        "sales": parts[2] if len(parts) > 2 else "",
        "car_name": parts[6] if len(parts) > 6 else "",
        "km": parts[9] if len(parts) > 9 else "",
        "plate": parts[10] if len(parts) > 10 else "",
        "vin": parts[11] if len(parts) > 11 else "",
        "heydlr_delivery": parts[12] if len(parts) > 12 else "",
        "color": parts[13] if len(parts) > 13 else "",
        "psource" : parts[14] if len(parts) > 14 else "",
        "address": parts[16] if len(parts) > 16 else "",
        "dealer_number": parts[17] if len(parts) > 17 else "",
        "dealer_phone": parts[18] if len(parts) > 18 else "",
        "region": parts[19] if len(parts) > 19 else "",
        "price": parts[22] if len(parts) > 22 else "0",
        "contract": parts[23] if len(parts) > 23 else "0",
        "fee": parts[24] if len(parts) > 24 else "0",
        "declaration": parts[25] if len(parts) > 25 else "0",
        "balance": parts[21] if len(parts) > 21 else "0",
        "buyer": parts[32] if len(parts) > 32 else "",
        "spec_num": parts[33] if len(parts) > 33 else "",
    }

    # 1. VIN 기반 연식 추출 (VIN의 뒤에서 8번째 자리)
    vin = data['vin'].strip().upper()
    if len(vin) >= 10:
        year_code = vin[-8] # 뒤에서 8번째
        data['year'] = VINYEAR_map.get(year_code, "")
    else:
        data['year'] = ""

    # 2. 컬러 매핑
    raw_color = data['color'].lower()
    data['color'] = COLOR_map.get(raw_color, data['color'].upper())

    # 3. 주소 기반 지역 자동 매핑
    for keyword, region_name in ADDRESS_REGION_MAP.items():
        if keyword in data['address']:
            data['region'] = region_name
            break
    # 데이터 추출 직후 브랜드 조회 로직 추가
    vin = data['vin'].strip().upper()
    if len(vin) >= 3:
        # brand.py의 함수 호출
        data['brand'] = brand.get_brand_from_vin(vin)
    else:
        data['brand'] = ""
        
    return data

def format_money(val):
    """숫자 형식 가공"""
    try:
        clean_val = re.sub(r'[^0-9]', '', str(val))
        return f"{int(clean_val):,}" if clean_val else "0"
    except:
        return "0"

def get_alt_car_name(raw_car_name, car_name_map):
    """
    긴 차명(raw_car_name)에서 매핑 테이블의 키가 포함되어 있는지 확인하여
    송금용 차명을 반환. (최장 일치 기준)
    """
    if not raw_car_name:
        return ""

    search_key = raw_car_name.upper()
    
    # 키 길이가 긴 순서대로 정렬 (예: '아반떼 AD'를 '아반떼'보다 먼저 검사)
    sorted_keys = sorted(car_name_map.keys(), key=len, reverse=True)

    for map_key in sorted_keys:
        if map_key in search_key:
            return car_name_map[map_key]
            
    return raw_car_name  # 매칭되는 게 없으면 원본 반환

# --- 0. 상단에 CBM 계산 함수 정의 ---
def calculate_cbm_logic():
    # 세션에서 값을 가져오되, 빈 문자열이면 0으로 처리
    try:
        l = float(st.session_state.get("v_l", 0) or 0)
        w = float(st.session_state.get("v_w", 0) or 0)
        h = float(st.session_state.get("v_h", 0) or 0)
        
        # mm 단위를 m 단위로 변환하여 계산 (L/1000 * W/1000 * H/1000)
        cbm_val = (l / 1000) * (w / 1000) * (h / 1000)
        
        # 소수점 두 자리까지 반올림하여 세션에 저장
        st.session_state["v_c"] = f"{cbm_val:.2f}"
    except ValueError:
        # 숫자가 아닌 값이 입력되었을 경우 처리
        st.session_state["v_c"] = "0.00"
