import re
import google_sheet_manager as gsm

def normalize_phone(phone):
    """전화번호에서 숫자만 추출"""
    return re.sub(r'[^0-9]', '', str(phone))

def search_dealer_info(contact_input):
    """
    연락처로 딜러 정보를 찾고, 사업자번호로 상사명까지 조회하여 딕셔너리로 반환
    """
    if not contact_input:
        return {"status": "error", "message": "연락처를 입력해주세요."}

    try:
        # 1. 딜러 연락처 시트 조회
        sheet = gsm.get_dealer_sheet()
        records = sheet.get_all_records()
        normalized_input = normalize_phone(contact_input)

        found_dealer = None
        for record in records:
            sheet_contact = normalize_phone(str(record.get("연락처", "")))
            if sheet_contact == normalized_input:
                found_dealer = record
                break

        if not found_dealer:
            return {"status": "empty", "message": f"연락처 '{contact_input}' 정보를 찾을 수 없습니다."}

        # 2. 사업자번호로 상사정보 시트 추가 조회
        biz_num = str(found_dealer.get("사업자번호", ""))
        company_name = "값 없음"
        
        if biz_num:
            company_sheet = gsm.get_company_sheet()
            company_records = company_sheet.get_all_values()
            for row in company_records:
                if len(row) >= 2 and str(row[0]).strip() == biz_num:
                    company_name = row[1]
                    break

        # 3. 결과 통합 반환
        return {
            "status": "success",
            "biz_num": biz_num,
            "address": found_dealer.get("주소", ""),
            "acc_o": found_dealer.get("차량대계좌", ""),
            "acc_fee": found_dealer.get("매도비계좌", ""),
            "sender": found_dealer.get("입금자명", ""),
            "company": company_name
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
