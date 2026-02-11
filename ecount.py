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
    """로그인 세션 획득 (성공했던 sboapi 주소 유지)"""
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
    """알려주신 정확한 URL로 품목 등록 실행"""
    # [수정] 알려주신 테스트용 엔드포인트 적용
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/SaveBasicProduct?SESSION_ID={session_id}"
    
    def to_float(val):
        try:
            import re
            if not val: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    l, w, h = to_float(data.get("length", 0)), to_float(data.get("width", 0)), to_float(data.get("height", 0))
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    # API 전송 데이터 (이카운트 품목등록 표준 필드)
    payload = {
        "BasicProduct": {
            "PROD_CD": data.get("vin"),             # 품목코드
            "PROD_DES": data.get("car_name_remit"), # 품목명
            "UNIT": "EA",
            "COL_1": data.get("brand"),             # 추가문자형식1
            "TXT_U_1": str(sheet_no),               # 문자형추가항목1
            "TXT_U_2": data.get("plate"),           # 문자형추가항목2
            "TXT_U_3": data.get("km"),              # 문자형추가항목3
            "TXT_U_4": data.get("color"),           # 문자형추가항목4
            "TXT_U_5": data.get("year"),            # 문자형추가항목5
            "TXT_U_6": "",                          # 제원관리번호 (빈칸)
            "DT_1": datetime.now().strftime("%Y%m%d"), # 추가일자형식1
            "NUM_U_2": l,                           # 숫자형추가항목2
            "NUM_U_3": w,                           # 숫자형추가항목3
            "NUM_U_4": h,                           # 숫자형추가항목4
            "NUM_U_5": 0,                           # 숫자형추가항목5
            "NUM_U_6": cmb_val,                     # 숫자형추가항목6 (CMB)
            "NUM_U_7": 1,                           # 숫자형추가항목7
            "NUM_U_8": 1                            # 숫자형추가항목8
        }
    }
    
    try:
        # 이카운트 V2는 보통 Bulk 형태의 요청을 받으므로 리스트로 감싸야 할 수도 있으나, 
        # 단일 품목 등록 규격에 맞춰 전송합니다.
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신 오류: {str(e)}"}
