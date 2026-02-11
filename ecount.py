import requests
import json
from datetime import datetime

# 이카운트 API 설정 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD" 

def get_session_id():
    """OAPILogin 방식을 사용하여 SESSION_ID를 가져옵니다."""
    # 요청하신 URL 구조 적용
    login_url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/OAPILogin"
    
    payload = {
        "COM_CODE": COM_CODE,
        "USER_ID": USER_ID,
        "API_CERT_KEY": API_CERT_KEY
    }
    
    try:
        # 이카운트 서버와의 연결을 시도합니다.
        response = requests.post(
            login_url, 
            data=json.dumps(payload), 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        res_data = response.json()
        
        # OAPILogin 결과 구조에 맞춰 토큰 추출
        if res_data.get("Status") == "200":
            # 데이터 구조가 다를 수 있으므로 안전하게 추출
            return res_data["Data"]["Datas"]["Token"]
        else:
            print(f"로그인 실패: {res_data.get('Message')}")
            return None
            
    except Exception as e:
        print(f"연결 오류: {e}")
        return None

def register_item(data, session_id, sheet_no):
    """품목 등록 API (SESSION_ID 사용)"""
    # 품목 등록 주소는 일반적으로 api{ZONE} 형식을 따릅니다.
    url = f"https://api{ZONE}.ecount.com/OAPI/V2/InventoryItem/SaveInventoryItem?SESSION_ID={session_id}"
    
    # [이전과 동일한 payload 구성]
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
            "NUM_U_7": 1,
            "NUM_U_8": 1
            # 필요한 추가 필드들을 여기에 포함하세요.
        }
    }
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"연결 실패: {str(e)}"}
