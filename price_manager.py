import re

"""
금액 포맷팅, 파싱 및 정산 계산 전용 모듈
"""

def format_number(value):
    """
    숫자를 억/만원 단위로 변환
    예: 150000000 -> "1억 5,000만원"
    """
    try:
        # 콤마 제거 후 정수 변환
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
    금액 문자열을 숫자로 변환 (천원 단위 포함 대응)
    예: "1억 5,000만원" -> 150000000
    """
    if not value: return 0
    try:
        # 1. 쉼표 및 공백 제거
        val_str = str(value).replace(",", "").replace(" ", "").strip()
        
        # 2. 단위별 합산 로직
        total = 0
        if "억" in val_str:
            parts = val_str.split("억")
            total += int(parts[0]) * 100000000
            val_str = parts[1] if len(parts) > 1 else ""
            
        if "만원" in val_str:
            val_str = val_str.replace("만원", "")
            if val_str: total += int(val_str) * 10000
            val_str = ""
        elif "만" in val_str:
            parts = val_str.split("만")
            if parts[0]: total += int(parts[0]) * 10000
            val_str = parts[1] if len(parts) > 1 else ""

        # 남은 숫자(원 단위) 처리
        final_digit = re.sub(r'[^0-9]', '', val_str)
        if final_digit:
            total += int(final_digit)
            
        return total if total > 0 else (int(final_digit) if final_digit else 0)
    except:
        return 0


def calculate_total(price, invoice, selling):
    """
    총액(TOTAL) 계산: 차량대 + 계산서X + 매도비
    """
    price_num = parse_money(price)
    invoice_num = parse_money(invoice)
    selling_num = parse_money(selling)
    
    return price_num + invoice_num + selling_num


def calculate_balance(total_str, contract_input):
    """
    잔금 계산: (합계) - (계약금 * 10000)
    """
    total_num = parse_money(total_str)
    contract_num = get_clean_deposit(contract_input)
    
    return total_num - contract_num


def get_clean_deposit(v_deposit):
    """
    계약금 입력값에서 숫자만 뽑아 무조건 '만원' 단위 정수로 반환
    예: "100" -> 1000000, "100만원" -> 1000000
    """
    try:
        if not v_deposit:
            return 0
        # 숫자만 추출
        clean = re.sub(r'[^0-9]', '', str(v_deposit))
        return int(clean) * 10000 if clean else 0
    except:
        return 0

def calculate_declaration(price_str):
    """
    차량대금 기반 DECLARATION(관세청 신고가) 자동 계산 로직
    - 백만 단위 절삭 금액의 10% 계산
    - 최대 100,000원 제한
    """
    amount = parse_money(price_str)
    
    if amount <= 0:
        return 0

    # 로직 적용: 백만 단위 절삭 (예: 8,340,000 -> 8,000,000)
    trimmed_amount = (amount // 1000000) * 1000000
    
    # 10% 계산 (예: 8,000,000 -> 800,000) -> 다시 단위 조정 로직 적용
    # 기존 로직: (trimmed_amount * 0.1) // 10000 * 1000
    # 예: 8,340,000원 -> 8,000,000원 -> 800,000원 -> 80,000원
    declaration = (trimmed_amount * 0.1) // 10000 * 1000
    
    # 최대 10만원 제한
    return int(min(declaration, 100000))
