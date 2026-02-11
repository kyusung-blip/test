import requests
import json
import urllib3

# SSL 인증서 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD" 

def get_session_id():
    """로그인 접속만 확인하는 테스트 함수"""
    
    # [시도 1] 테스트용 SBO 서버 (안될 경우 주석 처리하고 시도 2 사용)
    login_url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/OAPILogin"
    
    # [시도 2] 공용 게이트웨이 서버 (시도 1이 에러나면 아래 주석을 풀고 위 주석 처리)
    # login_url = "https://oapi.ecount.com/OAPI/V2/OAPILogin"
    
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
            verify=False,  # 보안 검증 우회
            timeout=10
        )
        return response.json() # 전체 응답을 그대로 반환해서 확인
            
    except Exception as e:
        return {"Status": "Error", "Message": str(e)}
