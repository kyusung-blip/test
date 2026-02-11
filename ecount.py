import requests
import json
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 설정 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD" 

def get_session_id():
    """로그인 세션 획득"""
    login_url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/OAPILogin"
    payload = {
        "COM_CODE": COM_CODE,
        "USER_ID": USER_ID,
        "API_CERT_KEY": API_CERT_KEY,
        "LAN_TYPE": "ko-KR",
        "ZONE": ZONE 
    }
    try:
        response = requests.post(login_url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            return res_data["Data"]["Datas"]["SESSION_ID"]
        return None
    except:
        return None

def register_item(data, session_id, sheet_no):
    """매뉴얼 표준 사양에 맞춘 품목 등록 로직"""
    # 1. URL 설정
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/SaveBasicProduct?SESSION_ID={session_id}"
    
    # 2. 숫자 계산 (길이/너비/높이가 문자열로 올 경우 대비)
    def to_float(val):
        try:
            import re
            if not val: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    l, w, h = to_float(data.get("length", 0)), to_float(data.get("width", 0)), to_float(data.get("height", 0))
    # CMB 계산 (길이1/1000 x 너비/1000 x 높이/1000)
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    # 3. 매뉴얼 규격에 맞춘 Payload 구성 (중요: List 형태)
    payload = {
        "BasicProductList": [
            {
                "LineNo": "1",
                "PROD_CD": str(data.get("vin", "")),      # 품목코드 (VIN)
                "PROD_DES": str(data.get("car_name_remit", "")), # 품목명 (차명)
                "UNIT": "EA",
                "COL_1": str(data.get("brand", "")),      # 추가문자형식1 (BRAND)
                "TXT_U_1": str(sheet_no),                 # 문자형추가항목1 (NO)
                "TXT_U_2": str(data.get("plate", "")),    # 문자형추가항목2 (차량번호)
                "TXT_U_3": str(data.get("km", "")),       # 문자형추가항목3 (km)
                "TXT_U_4": str(data.get("color", "")),    # 문자형추가항목4 (color)
                "TXT_U_5": str(data.get("year", "")),     # 문자형추가항목5 (연식)
                "TXT_U_6": "",                            # 문자형추가항목6 (제원번호)
                "DT_1": datetime.now().strftime("%Y%m%d"), # 추가일자형식1 (DATE)
                "NUM_U_2": l,                             # 숫자형추가항목2 (길이)
                "NUM_U_3": w,                             # 숫자형추가항목3 (너비)
                "NUM_U_4": h,                             # 숫자형추가항목4 (높이)
                "NUM_U_5": 0,                             # 숫자형추가항목5 (총중량)
                "NUM_U_6": round(cmb_val, 4),             # 숫자형추가항목6 (CMB)
                "NUM_U_7": 1,                             # 숫자형추가항목7 (유로)
                "NUM_U_8": 1                              # 숫자형추가항목8 (달러)
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신 오류: {str(e)}"}
