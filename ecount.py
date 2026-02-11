import requests
import json
from datetime import datetime
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD" 

def get_session_id():
    """성공 확인된 SBO URL과 페이로드로 세션 획득"""
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
        
        # [수정] 이카운트 응답의 Status는 숫자 200일 수 있으므로 유연하게 체크
        if str(res_data.get("Status")) == "200":
            # 응답 구조: Data -> Datas -> SESSION_ID
            return res_data["Data"]["Datas"]["SESSION_ID"]
        return None
    except:
        return None

def register_item(data, session_id, sheet_no):
    """발급받은 SESSION_ID로 품목 등록"""
    # 전표/품목 등록도 SBO 서버 주소를 사용해야 합니다.
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/InventoryItem/SaveInventoryItem?SESSION_ID={session_id}"
    
    # 숫자형 정제 (CMB 계산용)
    def to_float(val):
        try:
            import re
            if not val: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    l = to_float(data.get("length", 0))
    w = to_float(data.get("width", 0))
    h = to_float(data.get("height", 0))
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    # 요청하신 필드 매핑 적용
    payload = {
        "InventoryItem": {
            "PROD_CD": data.get("vin"),             # 품목코드: VIN
            "PROD_DES": data.get("car_name_remit"), # 품목명: 차명(송금용)
            "UNIT": "EA",
            "COL_1": data.get("brand"),             # BRAND (추가문자형식1)
            "TXT_U_1": str(sheet_no),               # NO (문자형추가1)
            "TXT_U_2": data.get("plate"),           # PLATE (문자형추가2)
            "TXT_U_3": data.get("km"),              # km (문자형추가3)
            "TXT_U_4": data.get("color"),           # COLOR (문자형추가4)
            "TXT_U_5": data.get("year"),            # YEAR (문자형추가5)
            "DT_1": datetime.now().strftime("%Y%m%d"), # DATE (추가일자1)
            "NUM_U_2": l,                           # 길이
            "NUM_U_3": w,                           # 너비
            "NUM_U_4": h,                           # 높이
            "NUM_U_6": cmb_val,                     # CMB
            "NUM_U_7": 1,                           # 유로환율
            "NUM_U_8": 1                            # 달러환율
        }
    }
    
    try:
        # 품목 등록 시에도 json 인자를 사용하고 verify=False 적용
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신 오류: {str(e)}"}
