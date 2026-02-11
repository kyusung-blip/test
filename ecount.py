import requests
import json
from datetime import datetime

# 이카운트 API 설정 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD"  # 확인된 ZONE 값

def get_session_id():
    """보내주신 공식 JSON 형식을 사용하여 세션 토큰을 가져옵니다."""
    login_url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/OAPILogin"
    
    # 요청하신 형식대로 데이터 구성
    payload = {
        "COM_CODE": COM_CODE,
        "USER_ID": USER_ID,
        "API_CERT_KEY": API_CERT_KEY,
        "LAN_TYPE": "ko-KR",  # 언어 설정 추가
        "ZONE": ZONE          # ZONE 정보 추가
    }
    
    try:
        response = requests.post(
            login_url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        res_data = response.json()
        
        # 성공 시 Token 추출
        if res_data.get("Status") == "200":
            # Data -> Datas -> Token 구조 확인
            return res_data["Data"]["Datas"]["Token"]
        else:
            # 실패 시 서버 메시지 출력 (디버깅용)
            print(f"로그인 실패: {res_data.get('Message')}")
            return None
            
    except Exception as e:
        print(f"연결 오류: {e}")
        return None

def register_item(data, session_id, sheet_no):
    """품목 등록 API (SESSION_ID 파라미터 사용)"""
    url = f"https://api{ZONE}.ecount.com/OAPI/V2/InventoryItem/SaveInventoryItem?SESSION_ID={session_id}"
    
    # 숫자형 정제 함수
    def to_float(val):
        try:
            import re
            if not val: return 0.0
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    l, w, h = to_float(data.get("length", 0)), to_float(data.get("width", 0)), to_float(data.get("height", 0))
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    # API 필드 매핑
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
        response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신 오류: {str(e)}"}
