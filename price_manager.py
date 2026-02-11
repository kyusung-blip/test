# price_manager.py
"""
금액 포맷팅 및 파싱 전용 모듈
"""

def format_number(value):
    """
    숫자를 억/만원 단위로 변환
    예: 150000000 -> "1억 5,000만원"
    """
    try:
        value = int(str(value).replace(",", "").strip())

        if value >= 100000000 and value % 10000 == 0:
            eok = value // 100000000
            man = (value % 100000000) // 10000
            if man == 0:
                return f"{eok}억"
            else:
                return f"{eok}억 {man:,}만원"
        elif value >= 10000 and value % 10000 == 0:
            return f"{value // 10000:,}만원"
        else:
            return f"{value:,}원"
    except (ValueError, TypeError):
        return str(value)


def parse_money(value):
    """
    금액 문자열을 숫자로 변환
    예: "1억 5,000만원" -> 150000000
    """
    try:
        value = str(value).replace(",", "").strip()
        if "억" in value:
            parts = value.split("억")
            eok = int(parts[0]) * 100000000
            man = int(parts[1].replace("만원", "").replace("원", "").strip()) * 10000 if len(parts) > 1 and parts[1].strip() else 0
            return eok + man
        elif value.endswith("만원"):
            return int(value.replace("만원", "")) * 10000
        elif value.endswith("원"):
            return int(value.replace("원", ""))
        else:
            return int(value)
    except:
        return 0


def calculate_total(price, invoice, selling):
    """
    총액(TOTAL) 계산: 차량대 + 계산서X + 매도비
    
    Args:
        price: 차량대
        invoice: 계산서X
        selling: 매도비
    
    Returns:
        int: 총액
    """
    price_num = parse_money(price) if price else 0
    invoice_num = parse_money(invoice) if invoice else 0
    selling_num = parse_money(selling) if selling else 0
    
    total = price_num + invoice_num + selling_num
    return total


def calculate_balance(total_str, contract_input):
    """
    잔금 계산: (합계) - (계약금 * 10000)
    contract_input은 사용자가 "100" 혹은 "100만원"이라고 입력해도 
    숫자 100만 추출하여 1,000,000원으로 계산합니다.
    """
    # 1. 합계 금액 파싱
    total_num = parse_money(total_str)
    
    # 2. 계약금 처리 (숫자만 추출)
    try:
        # 문자열에서 숫자만 남기기 (예: "100만원" -> "100")
        contract_clean = re.sub(r'[^0-9]', '', str(contract_input))
        if contract_clean:
            contract_num = int(contract_clean) * 10000 # 무조건 만원 단위
        else:
            contract_num = 0
    except:
        contract_num = 0
        
    return total_num - contract_num
