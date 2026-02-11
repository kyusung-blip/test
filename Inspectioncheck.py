import google_sheet_manager as gsm

def fetch_inspection_status(plate_number):
    """
    차량번호로 인스펙션 시트의 6열 블록 구조를 검색하여 상태 반환
    - 카스토리 -> C
    - 내용 없음 -> X
    - 기타 내용 있음 -> S
    - 검색 실패 시 -> X
    """
    if not plate_number:
        return "X"

    # 검색 최적화를 위해 공백 제거 및 소문자화
    target_plate = plate_number.strip().lower().replace(" ", "")

    try:
        sheet = gsm.get_inspection_data_sheet()
        all_values = sheet.get_all_values()

        if not all_values:
            return "X"

        # 최신 데이터를 찾기 위해 아래(마지막 행)에서부터 위로 검색
        for i in reversed(range(1, len(all_values))):
            row = all_values[i]
            
            # 한 행 내에서 6열 간격으로 블록 순회 (B, H, N, T, Z... 순서)
            # 인덱스로는 1, 7, 13, 19, 25...
            for col_start in range(1, len(row), 6):
                
                # 블록의 차량번호 위치 (B, H, N...)
                plate_idx = col_start
                # 블록의 인스펙션 내용 위치 (D, J, P...) -> 차량번호 열 + 2
                content_idx = col_start + 2

                # 현재 행의 길이가 내용 인덱스보다 짧으면 해당 블록 스킵
                if len(row) <= content_idx:
                    continue

                sheet_plate = row[plate_idx].strip().lower().replace(" ", "")
                
                # 차량번호 일치 여부 확인
                if sheet_plate and sheet_plate == target_plate:
                    inspection_content = row[content_idx].strip()
                    
                    # 상태 판별 로직
                    if inspection_content == "카스토리":
                        return "C"
                    elif not inspection_content:
                        return "X"
                    else:
                        return "S"

        # 모든 행을 다 돌아도 없으면 X 반환
        return "X"

    except Exception as e:
        print(f"Inspection Check Error: {e}")
        return "Error"
