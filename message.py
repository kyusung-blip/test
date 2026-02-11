import re
import price_manager as pm

def handle_confirm(data, m_type="confirm"):
    """
    data: buyprogram.py에서 입력받은 값들의 딕셔너리
    m_type: 버튼 종류 ('confirm', 'salesteam', 'inspection', 'sms', 'outsource', 'share_address')
    """
    
    year = data.get('year', '')
    car_name = data.get('car_name', '') or "차량명"
    plate = data.get('plate', '')
    
    # 값 정규화 (0, 0원, 0만원 등 빈 값 처리)
    def normalize(val):
        val = str(val).strip()
        if re.fullmatch(r'0|0원|0만원|', val):
            return ""
        return val

    raw_price = normalize(data.get('price', ""))
    raw_fee = normalize(data.get('fee', ""))
    raw_contract = normalize(data.get('contract_x', "")) # 계산서X

    title_line = f"{year} {car_name}"

    # 1. 아웃소싱 메시지
    if m_type == "outsource":
        result = f"요청자 : {data.get('sales', '')}\n차명 : {car_name}\n차량번호 : {plate}\n주소 : {data.get('address', '')}\n차주 연락처 : {data.get('dealer_phone', '')}\n\n{data.get('region', '')} 한대 부탁드립니다~!\n\n{data.get('site', '')}\n"
    
    # 2. 주소공유 메시지
    elif m_type == "share_address":
        result = f"Sales Team : {data.get('sales', '')}\nModel : {car_name}\nPlate : {plate}\nCar Address : {data.get('address', '')}\nDealer Phone : {data.get('dealer_phone', '')}\n\n{data.get('site', '')}\n"
    
    # 3. 일반 안내 문자들 (수출말소기준)
    else:
        # 조건별 금액 라인 생성
        if raw_price and raw_fee and raw_contract:
            content = f"계산서(O) : {raw_price}\n계산서(X) : {raw_contract}\n매도비 : {raw_fee}"
        elif raw_price and raw_contract and not raw_fee:
            content = f"계산서(O) : {raw_price}\n계산서(X) : {raw_contract}"
        elif raw_price and raw_fee and not raw_contract:
            content = f"차량대 : {raw_price}\n매도비 : {raw_fee}\n세금계산서 전액발행"
        else:
            fee_txt = f"매도비포함 {raw_price}" if not raw_fee else f"차량대 : {raw_price}\n매도비 : {raw_fee}"
            content = f"{fee_txt}\n세금계산서 전액발행"

        result = f"{title_line}\n{plate}\n\n수출말소기준\n{content}"

        # 버튼별 꼬리말 추가
        if m_type == "salesteam":
            result += "\n\n세일즈팀에서 금일 방문 예정입니다~!"
        elif m_type == "inspection":
            result += "\n\n검수자 배정 후 연락드리겠습니다~!"
        elif m_type == "sms":
            pass # 문자 버튼은 추가 문구 없음
        else: # 확인후 (confirm)
            result += "\n\n확인 후 연락드리겠습니다~!"
    
    print(f"DEBUG: 생성된 메시지 -> {result}")
    return result
