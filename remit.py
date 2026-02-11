import re
import price_manager as pm

def handle_remit(data, r_type="일반매입"):
    """
    data: buyprogram.py에서 수집한 입력값 딕셔너리
    r_type: 버튼 종류
    """
    # 기본 정보 추출
    plate = data.get('plate', '')
    year = data.get('year', '')
    car_name = data.get('car_name', '')
    vin = data.get('vin', '')
    address = data.get('address', '')
    phone = data.get('dealer_phone', '')
    account = data.get('price_acc', '')    # 차량대/계산서O 계좌
    notbill = data.get('notbill_acc', '')  # 계산서X 계좌
    feeaccount = data.get('fee_acc', '')   # 매도비 계좌
    sender_name = data.get('sender_name', '').strip()
    brand = data.get('brand', '')
    
    # 오토위니/헤이딜러 전용
    company = data.get('company', '')
    ex_date = data.get('ex_date', '')
    ex_rate = data.get('ex_rate', '')
    usd_price = data.get('usd_price', '')
    won_price = data.get('won_price', '')
    dealer_num = data.get('dealer_number', '')
    h_type = data.get('h_type', '')
    h_id = data.get('h_id', '')
    h_delivery = data.get('h_delivery', '')

    # 금액 데이터 (포맷팅된 문자열)
    raw_price = data.get('price', '0')
    raw_fee = data.get('fee', '0')
    raw_contract_x = data.get('contract_x', '0')
    raw_total = data.get('total', '0')
    raw_deposit = data.get('deposit', '0')
    raw_balance = data.get('balance', '0')

    # 숫자 계산용
    def is_zero(val):
        clean = re.sub(r'[^0-9]', '', str(val))
        return clean == "" or clean == "0"

    price_val = pm.parse_money(raw_price)
    deposit_val = pm.get_clean_deposit(raw_deposit)
    
    # 차량대 - 계약금 계산 (문자열 포맷팅)
    diff_val = price_val - deposit_val
    raw_diff = pm.format_number(diff_val)

    message = "*서북인터내셔널"
    name_suffix = "로" if sender_name == "차량번호" else "으로"

    # --- 로직 시작 ---
    if r_type == "계약금":
        if not is_zero(raw_price) and not is_zero(raw_contract_x):
            # 분리 매입
            message += f" 주식회사*\n\n차번호: {plate} // {year} {car_name}\nVIN: {vin}\n\n사업자번호: {dealer_num}\n주소: {address}\n번호: {phone}\n\n계산서(O): {raw_price}\n계산서(X): {raw_contract_x}\n"
            if not is_zero(raw_fee): message += f"매도비: {raw_fee}\n"
            message += f"합계: {raw_total}\n\n계좌\n계산서(O): {account}\n계산서(X): {notbill}\n"
            if not is_zero(raw_fee) and feeaccount: message += f"매도비: {feeaccount}\n"
            
            fee_part = f"+{raw_fee}" if not is_zero(raw_fee) else ""
            final_calc = f"{raw_diff}+{raw_contract_x}{fee_part}"
            message += f"\n{sender_name}{name_suffix} 계약금 송금 부탁드립니다.\n\n@@@계약금 {raw_deposit} \n@@@잔금 {final_calc}"
        else:
            # 일반 매입
            fee_line = "매도비포함" if is_zero(raw_fee) else f"매도비: {raw_fee}"
            message += f" 주식회사*\n\n차번호: {plate} // {year} {car_name}\nVIN: {vin}\n\n사업자번호: {dealer_num}\n주소: {address}\n번호: {phone}\n\n차량대: {raw_price}\n{fee_line}\n합계: {raw_total}\n\n계좌\n차량대: {account}\n"
            if not is_zero(raw_fee) and feeaccount: message += f"매도비: {feeaccount}\n"
            
            fee_part = f"+{raw_fee}" if not is_zero(raw_fee) else ""
            final_calc = f"{raw_diff}{fee_part}"
            message += f"\n{sender_name}{name_suffix} 계약금 송금 부탁드립니다.\n\n@@@계약금 {raw_deposit} \n@@@잔금 {final_calc}"

    elif r_type == "폐자원매입":
        message += f" 주식회사*\n\n@@@폐자원매입@@@\n\n차번호: {plate} // {year} {car_name}\nVIN: {vin}\n주소: {address}\n번호: {phone}\n\n차량대: {raw_price}\n\n계좌(차주 개인확인, 차주 계좌로 직접송금)\n차량대: {account}\n\n{sender_name}{name_suffix} 송금 부탁드립니다."

    elif r_type == "송금완료":
        fee_line = "매도비포함" if is_zero(raw_fee) else f"매도비: {raw_fee}"
        message += f" 주식회사*\n\n@@@송금완료@@@\n\n차번호: {plate} // {year} {car_name}\nVIN: {vin}\n\n사업자번호: {dealer_num}\n주소: {address}\n번호: {phone}\n\n차량대: {raw_price}\n{fee_line}\n합계: {raw_total}\n\n계좌\n차량대: {account}\n"
        if feeaccount and not is_zero(raw_fee): message += f"매도비: {feeaccount}\n"
        message += f"\n{sender_name}{name_suffix} 송금 부탁드립니다."

    elif r_type == "오토위니":
        message += f"-{company}*\n*서북인터내셔널-{company}*\n\n모델: {year} {brand} {car_name}\nVIN: {vin}\n\n회사: {company}\n번호: {phone}\n차량대금: {usd_price} USD\n\n외화계좌: {account}\n영세율 계산서 거래\n구매확인서 발급\n\n환율금액: {ex_date} 기준 {ex_rate}원\n{won_price}원\n\n*서북인터내셔널-{company}*"

    elif r_type == "헤이딜러":
        h_id_display = h_id if h_id != "선택 안함" else "ID 미선택"
        message = f"*서북인터내셔널 주식회사 *\n\n@@@폐자원매입@@@\n\n헤이딜러 {h_type} (사전판매완료 id: {h_id_display})\n"
        message += f"차번호: {plate} // {year} {car_name}\nVIN: {vin}\n"
        if h_type == "일반":
            message += f"주소: {address}\n번호: {phone}\n\n차량가: {raw_price}\n계좌: {account}\n\n차량번호로 송금 부탁드립니다."
        else: # 제로, 바로낙찰
            message += f"\n차대금 송금 부탁드립니다~!\n\n차대금: {raw_price}\n입금계좌:\n{account}\n\n탁송 출발 2시간 전 입금 바랍니다.\n일정: {h_delivery}"

    else: # 일반매입 (Default)
        # 계약금 로직과 유사하되 '송금 부탁드립니다'로 마무리
        message += f" 주식회사*\n\n차번호: {plate} // {year} {car_name}\n..." # (중략 - 일반매입 양식)
        
    return message
