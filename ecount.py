# ecount.py
import requests
import json
from datetime import datetime

# 이카운트 API 설정 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "KR" 

def get_session_id():
    """이카운트 API 세션 토큰을 가져옵니다."""
    url = f"https://api{ZONE}.ecount.com/OAPI/V2/Common/Token/GetToken"
    payload = {
        "COM_CODE": COM_CODE,
        "USER_ID": USER_ID,
        "API_CERT_KEY": API_CERT_KEY
    }
    try:
        response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        res_data = response.json()
        if res_data.get("Status") == "200":
            return res_data["Data"]["Datas"]["Token"]
        return None
    except Exception as e:
        return None

def register_item(data, session_id, sheet_no):
    """이카운트 신규 품목 등록 API"""
    url = f"https://api{ZONE}.ecount.com/OAPI/V2/InventoryItem/SaveInventoryItem?SESSION_ID={session_id}"
    
    def to_float(val):
        try:
            import re
            if not val: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    length = to_float(data.get("length", 0))
    width = to_float(data.get("width", 0))
    height = to_float(data.get("height", 0))
    cmb_val = (length / 1000) * (width / 1000) * (height / 1000)

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
            "TXT_U_6": "",
            "DT_1": datetime.now().strftime("%Y%m%d"),
            "NUM_U_2": length,
            "NUM_U_3": width,
            "NUM_U_4": height,
            "NUM_U_5": 0,
            "NUM_U_6": cmb_val,
            "NUM_U_7": 1,
            "NUM_U_8": 1
        }
    }
    try:
        response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": str(e)}

def register_purchase(data, session_id):
    """구매 전표 입력 함수 (필요시 사용)"""
    # ... 기존에 드린 register_purchase 로직 ...
    pass
