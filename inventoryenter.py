import streamlit as st
import platform
import re
from datetime import datetime
import google_sheet_manager as gsm
import price_manager as pm

def get_today_str():
    """OS 환경에 맞게 m/d 형식 날짜 반환"""
    if platform.system() == 'Windows':
        return datetime.today().strftime("%#m/%#d")
    return datetime.today().strftime("%-m/%-d")

def run_integrated_registration(data):
    """인벤토리(Yard)와 메인(2026) 시트 통합 등록 함수"""
    try:
        today = get_today_str()
        
        # 1. 공통 데이터 추출
        plate = data.get('plate', '').strip()
        vin = data.get('vin', '').strip()
        year = data.get('year', '')
        car_name = data.get('car_name_remit', '') # 송금용 차명
        inspection_val = data.get('inspection', '?')
        
        # 2. 메인 시트(2026) 중복 검사
        sheet_main = gsm.get_main_2026_sheet()
        all_main_values = sheet_main.get_all_values()
        
        # C열(차번호, index 2), D열(VIN, index 3) 추출
        existing_plates = [row[2].strip().lower() for row in all_main_values if len(row) > 2]
        existing_vins = [row[3].strip().lower() for row in all_main_values if len(row) > 3]
        
        is_duplicate = (plate.lower() in existing_plates if plate else False) or \
                       (vin.lower() in existing_vins if vin else False)

        # 3. 인벤토리(Yard Status) 데이터 구성
        sheet_yard = gsm.get_inventory_sheet()
        
        # 사원명 매핑
        sales_map = {
            "OSWALDO": "OSW", "코랄": "CORAL", "자파르": "ZAFAR", "엔젤": "ANGEL",
            "VIKTOR": "VIKTOR", "제프": "JEFF", "임진수": "JINSU", "임진수(L)": "큰사장님"
        }
        raw_sales = data.get('sales', '').upper()
        sales_mapped = sales_map.get(raw_sales, raw_sales)

        # I열(잔금 정보) 구성
        h_type = data.get('h_type', '선택')
        h_delivery = data.get('h_delivery', '')
        deposit_raw = data.get('deposit', '0')
        
        # 잔금 텍스트 생성 로직
        price_val = pm.parse_money(data.get('price', '0'))
        deposit_val = pm.get_clean_deposit(deposit_raw)
        balance_only = price_val - deposit_val
        
        fee_raw = data.get('fee', '0')
        fee_part = f"+{fee_raw}" if pm.parse_money(fee_raw) > 0 else ""
        contract_raw = data.get('contract_x', '0')
        contract_part = f"+{contract_raw}" if pm.parse_money(contract_raw) > 0 else ""
        
        balance_text = f"잔금 {pm.format_number(balance_only)}{contract_part}{fee_part}"

        # I열 결정 우선순위
        inventory_i_col = ""
        if h_type != "선택" and h_delivery:
            inventory_i_col = f"탁송 {h_delivery}"
        elif h_type == "선택" and pm.get_clean_deposit(deposit_raw) > 0:
            inventory_i_col = balance_text

        # K열(비고) 구성 (헤이딜러 정보 등)
        km_val = data.get('km', '')
        company_name = data.get('company', '').strip()
        if company_name:
            inventory_k_col = f"영세율 {company_name}"
        else:
            h_suffix = ""
            h_id = data.get('h_id', '').replace("선택", "").strip()
            if h_type == "일반": h_suffix = f" 헤이딜러일반:{h_id} 폐자원 {plate}"
            elif h_type == "제로": h_suffix = f" 헤이딜러제로:{h_id} 폐자원 {plate}"
            elif h_type == "바로낙찰": h_suffix = f" 헤이딜러바로:{h_id} 폐자원 {plate}"
            inventory_k_col = f"{km_val}{h_suffix}"
        

        # Yard 시트 행 데이터 (A~Q)
        yard_row = [
            today, "1", data.get('region', ''), year, data.get('brand', ''),
            car_name, vin, data.get('color', '').upper(), inventory_i_col, 
            "", inventory_k_col, sales_mapped, data.get('country', '').upper(),
            data.get('buyer', '').upper(), "", "-", inspection_val
        ]
        
        # 4. Yard 시트 등록
        # 전체 시트의 A열 데이터를 가져와서 마지막 데이터가 있는 행 번호를 찾습니다.
        all_yard_data = sheet_yard.get_all_values()
        next_yard_row = len(all_yard_data) + 1
        
        # A열부터 Q열까지의 범위를 지정 (yard_row의 길이가 17이므로 A~Q)
        # 만약 데이터가 더 늘어난다면 범위를 조정하세요.
        yard_range = f"A{next_yard_row}:Q{next_yard_row}"
        sheet_yard.update(yard_range, [yard_row], value_input_option="USER_ENTERED")

        # 5. 메인 시트(2026) 등록 (중복 아닐 때만)
        if not is_duplicate:
            # 다음 빈 행 찾기 (C열 기준)
            c_col_values = [row[2] for row in all_main_values if len(row) > 2]
            next_row = len(c_col_values) + 1
            for i in reversed(range(len(c_col_values))):
                if c_col_values[i].strip():
                    next_row = i + 2
                    break
            
            # 메인 시트 데이터 (C~I열)
            main_values = [car_name, plate, vin, year, today, data.get('biz_name', ''), data.get('biz_num', '')]
            sheet_main.update(f"C{next_row}:I{next_row}", [main_values])
            
            # K, L, O열 (금액 및 신고가)
            invoice_val = pm.parse_money(data.get('price', '0')) + pm.parse_money(data.get('fee', '0'))
            sheet_main.update(f"K{next_row}", [[invoice_val]]) # J열(인덱스 기준 K)
            
            contract_x_val = pm.parse_money(data.get('contract_x', '0'))
            if contract_x_val > 0:
                sheet_main.update(f"L{next_row}", [[contract_x_val]])
                
            declaration_val = pm.parse_money(data.get('declaration', '0'))
            sheet_main.update(f"O{next_row}", [[declaration_val]])

            return {"status": "success", "message": "✅ 인벤토리 및 메인 시트에 등록되었습니다."}
        else:
            return {"status": "partial", "message": "⚠️ 인벤토리 등록 완료. 메인 시트는 중복(VIN/차번호)으로 건너뛰었습니다."}

    except Exception as e:
        return {"status": "error", "message": f"등록 실패: {str(e)}"}
