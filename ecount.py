import requests
import json
from datetime import datetime
import urllib3

# SSL 인증서 경고 무시 (테스트 서버 연결 안정성 확보)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD" 

def get_session_id():
    """테스트용 SBO API 엔드포인트를 사용하여 세션을 가져옵니다."""
    # 운영 서버 oapi 대신 알려주신 sboapi 주소를 사용합니다.
    login_url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/OAPILogin"
    
    payload = {
        "COM_CODE": COM_CODE,
        "USER_ID": USER_ID,
        "API_CERT_KEY": API_CERT_KEY,
        "LAN_TYPE": "ko-KR",
        "ZONE": ZONE 
    }
    
    try:
        response = requests.post(
            login_url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'},
            verify=False, # 테스트 서버는 인증서 이슈가 잦으므로 False 권장
            timeout=15
        )
        res_data = response.json()
        
        if res_data.get("Status") == "200":
            return res_data["Data"]["Datas"]["Token"]
        else:
            print(f"로그인 실패 응답: {res_data.get('Message')}")
            return None
            
    except Exception as e:
        print(f"테스트 서버 연결 오류: {e}")
        return None

def register_item(data, session_id, sheet_no):
    """품목 등록 API (테스트 서버용)"""
    # 등록 주소도 sboapi로 맞춰야 합니다.
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/InventoryItem/SaveInventoryItem?SESSION_ID={session_id}"
    
    # 숫자형 정제 (CMB)
    def to_float(val):
        try:
            import re
            if not val: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    l, w, h = to_float(data.get("length", 0)), to_float(data.get("width", 0)), to_float(data.get("height", 0))
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    payload = {
        "InventoryItem": {
            "PROD_CD": data.get("vin"),
            "PROD_DES": data.get("car_name_remit"),
            "UNIT": "EA",
            "COL_1": data.get("brand"),
            "TXT_U_1": str(sheet_no),
            "TXT_U_2": data.get("plate"),
            "TXT_U_3": data.get("km"),
            "TXT_U_4": data.get("color"),
            "TXT_U_5": data.get("year"),
            "DT_1": datetime.now().strftime("%Y%m%d"),
            "NUM_U_2": l, "NUM_U_3": w, "NUM_U_4": h,
            "NUM_U_6": cmb_val,
            "NUM_U_7": 1, "NUM_U_8": 1
        }
    }
    
    try:
        response = requests.post(
            url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'},
            verify=False,
            timeout=15
        )
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신 오류: {str(e)}"}
