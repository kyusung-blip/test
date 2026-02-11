import requests
import json
from datetime import datetime

# 이카운트 설정 (기존 정보 유지)
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "KR" 

def register_item(data, session_id, sheet_no):
    """이카운트 신규 품목 등록 API"""
    url = f"https://api{ZONE}.ecount.com/OAPI/V2/InventoryItem/SaveInventoryItem?SESSION_ID={session_id}"
    
    # 숫자 추출 및 계산 함수
    def to_float(val):
        try:
            import re
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    # CMB 계산 (길이/너비/높이가 빈칸이면 0)
    length = to_float(data.get("length", 0))
    width = to_float(data.get("width", 0))
    height = to_float(data.get("height", 0))
    cmb_val = (length / 1000) * (width / 1000) * (height / 1000)

    # API 전송 데이터 구조화
    payload = {
        "InventoryItem": {
            "PROD_CD": data.get("vin"),             # 품목코드: VIN
            "PROD_DES": data.get("car_name_remit"), # 품목명: 차명(송금용)
            "UNIT": "EA",
            
            # 문자형 항목
            "COL_1": data.get("brand"),             # 추가문자형식1: BRAND
            "TXT_U_1": str(sheet_no),               # 문자형추가1: NO (구글시트 B열)
            "TXT_U_2": data.get("plate"),           # 문자형추가2: PLATE
            "TXT_U_3": data.get("km"),              # 문자형추가3: km
            "TXT_U_4": data.get("color"),           # 문자형추가4: COLOR
            "TXT_U_5": data.get("year"),            # 문자형추가5: YEAR
            "TXT_U_6": "",                          # 문자형추가6: 제원관리번호 (빈칸)
            
            # 일자 항목
            "DT_1": datetime.now().strftime("%Y%m%d"), # 추가일자형식1: DATE
            
            # 숫자형 항목
            "NUM_U_2": length,                      # 숫자형추가2: 길이
            "NUM_U_3": width,                       # 숫자형추가3: 너비
            "NUM_U_4": height,                      # 숫자형추가4: 높이
            "NUM_U_5": 0,                           # 숫자형추가5: 총중량
            "NUM_U_6": cmb_val,                     # 숫자형추가6: CMB
            "NUM_U_7": 1,                           # 숫자형추가7: 유로환율
            "NUM_U_8": 1                            # 숫자형추가8: 달러환율
        }
    }
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"연결 실패: {str(e)}"}
