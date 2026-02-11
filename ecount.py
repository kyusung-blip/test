import requests
import json
from datetime import datetime
import urllib3

# SSL 경고 메시지 무시 설정 (Streamlit Cloud 환경 안정성 확보)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD" 

def get_session_id():
    """진단에서 성공한 메인 게이트웨이 주소를 사용합니다."""
    # oapiAD 대신 진단에 성공한 oapi 메인 주소를 사용합니다.
    login_url = "https://oapi.ecount.com/OAPI/V2/OAPILogin"
    
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
            verify=False,  # SSL 인증서 검증 건너뛰기 (연결 오류 해결용)
            timeout=15     # 타임아웃 시간을 넉넉히 설정
        )
        res_data = response.json()
        
        if res_data.get("Status") == "200":
            return res_data["Data"]["Datas"]["Token"]
        else:
            print(f"로그인 실패 응답: {res_data}")
            return None
            
    except Exception as e:
        # 에러 로그를 상세히 남깁니다.
        print(f"연결 실패 상세 원인: {str(e)}")
        return None

def register_item(data, session_id, sheet_no):
    """품목 등록 API"""
    # 품목 등록은 실제 데이터 서버를 가리켜야 합니다.
    url = f"https://api{ZONE}.ecount.com/OAPI/V2/InventoryItem/SaveInventoryItem?SESSION_ID={session_id}"
    
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
