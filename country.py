import google_sheet_manager as gsm

def handle_buyer_country(buyer_name, country_input):
    """
    바이어 이름으로 나라를 조회하거나 업데이트/추가합니다.
    """
    if not buyer_name:
        return {"status": "error", "message": "바이어 이름을 입력해주세요."}

    try:
        sheet = gsm.get_country_sheet()
        all_records = sheet.get_all_values()
        
        found_row_idx = None
        found_country = None

        # 1. 시트 전체를 돌며 바이어 검색
        for i, row in enumerate(all_records):
            if len(row) > 0 and row[0].strip().lower() == buyer_name.strip().lower():
                found_row_idx = i + 1  # 구글 시트는 1번부터 시작
                found_country = row[1].strip() if len(row) > 1 else ""
                break

        if found_row_idx:
            # ▶ 바이어 정보가 이미 있는 경우
            if not country_input:
                # 필드가 비어있으면 정보를 불러옴
                return {"status": "fetched", "country": found_country}
            
            elif country_input != found_country:
                # 입력된 나라가 시트와 다르면 업데이트
                sheet.update_cell(found_row_idx, 2, country_input)
                return {"status": "updated", "country": country_input}
            
            else:
                return {"status": "match", "country": found_country}
        
        else:
            # ▶ 바이어 정보가 없는 경우
            if not country_input:
                return {"status": "not_found", "message": "등록된 바이어가 아니며, 입력된 나라 정보도 없습니다."}
            else:
                # 새로 추가
                sheet.append_row([buyer_name, country_input])
                return {"status": "added", "country": country_input}

    except Exception as e:
        return {"status": "error", "message": str(e)}
