import re
import google_sheet_manager as gsm

def normalize_phone(phone):
    """전화번호 숫자만 추출"""
    if not phone: return ""
    return re.sub(r'[^0-9]', '', str(phone))

def search_dealer_info(contact_input):
    """기존과 동일: 연락처로 딜러 및 상사명 조회"""
    if not contact_input:
        return {"status": "error", "message": "연락처를 입력해주세요."}
    try:
        sheet = gsm.get_dealer_sheet()
        records = sheet.get_all_records()
        normalized_input = normalize_phone(contact_input)
        found_dealer = None
        for record in records:
            if normalize_phone(str(record.get("연락처", ""))) == normalized_input:
                found_dealer = record
                break
        if not found_dealer:
            return {"status": "empty", "message": "정보를 찾을 수 없습니다."}

        biz_num = str(found_dealer.get("사업자번호", "")).strip()
        company_name = "값 없음"
        if biz_num:
            company_sheet = gsm.get_company_sheet()
            company_records = company_sheet.get_all_values()
            for row in company_records:
                if len(row) >= 2 and str(row[0]).strip() == biz_num:
                    company_name = row[1]
                    break
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

def save_or_update_dealer(data):
    """
    기존 '계좌업데이트' 함수 로직 이식:
    변경된 항목만 찾아 메인 시트와 상사정보 시트를 각각 업데이트/추가함.
    """
    contact = normalize_phone(data.get('phone', ""))
    if not contact:
        return {"status": "error", "message": "연락처를 입력해주세요."}

    try:
        # 1. 메인 딜러 시트 (Sheet1) 작업
        sheet = gsm.get_dealer_sheet()
        records = sheet.get_all_records()
        headers = sheet.row_values(1)
        # 헤더명에 따른 열 번호 매핑 (사업자번호:3, 주소:4 ...)
        header_map = {header.strip(): idx + 1 for idx, header in enumerate(headers)}
        
        normalized_input = normalize_phone(contact)
        found_row_idx = None
        target_record = None

        for i, record in enumerate(records):
            if normalize_phone(str(record.get("연락처", ""))) == normalized_input:
                found_row_idx = i + 2
                target_record = record
                break

        update_count = 0
        
        if found_row_idx:
            # --- 기존 딜러 정보 수정 로직 ---
            fields_to_check = {
                "사업자번호": data.get("biz_num", ""),
                "주소": data.get("address", ""),
                "차량대계좌": data.get("acc_o", ""),
                "매도비계좌": data.get("acc_fee", ""),
                "입금자명": data.get("sender", "")
            }

            for key, new_val in fields_to_check.items():
                if str(target_record.get(key, "")).strip() != str(new_val).strip():
                    if key in header_map:
                        sheet.update_cell(found_row_idx, header_map[key], new_val)
                        update_count += 1
        else:
            # --- 신규 딜러 추가 로직 ---
            new_row = ["딜러명", contact, data.get("biz_num",""), data.get("address",""), 
                       data.get("acc_o",""), data.get("acc_fee",""), data.get("sender","")]
            sheet.append_row(new_row, value_input_option="USER_ENTERED")

        # 2. 상사 정보 시트 (상사정보) 작업
        comp_sheet = gsm.get_company_sheet()
        all_companies = comp_sheet.get_all_values()
        biz_num = data.get("biz_num", "").strip()
        biz_name = data.get("biz_name", "").strip()
        
        company_found = False
        company_updated = False

        if biz_num:
            for j, row in enumerate(all_companies):
                if len(row) > 0 and str(row[0]).strip() == biz_num:
                    company_found = True
                    current_name = row[1].strip() if len(row) > 1 else ""
                    if current_name != biz_name:
                        comp_sheet.update_cell(j + 1, 2, biz_name)
                        company_updated = True
                    break
            
            if not company_found:
                comp_sheet.append_row([biz_num, biz_name], value_input_option="USER_ENTERED")
                company_updated = True

        # 3. 결과 메시지 조립
        if not found_row_idx:
            return {"status": "success", "message": "신규 딜러 정보가 추가되었습니다."}
        
        if company_updated and update_count > 0:
            msg = "기존 딜러 정보 및 상사 정보가 수정되었습니다."
        elif company_updated:
            msg = "상사 정보만 수정되었습니다."
        elif update_count > 0:
            msg = "기존 딜러 정보가 수정되었습니다."
        else:
            msg = "변경사항이 없습니다."
            
        return {"status": "success", "message": msg}

    except Exception as e:
        return {"status": "error", "message": f"처리 중 오류 발생: {str(e)}"}
