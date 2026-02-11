import requests
import json

# 이카운트 API 설정 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "CN" # 한국/중국 서버 권역 (보통 CN 또는 KR)

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
        
        # 성공 시 데이터 구조: Data -> Datas -> Token
        if res_data.get("Status") == "200":
            return res_data["Data"]["Datas"]["Token"]
        else:
            print(f"로그인 실패: {res_data.get('Message')}")
            return None
    except Exception as e:
        print(f"API 연결 오류: {e}")
        return None

def register_purchase(data, session_id):
    """
    매입전표1을 생성합니다. 
    필드명(BulkDatas)은 이카운트 표준 양식을 따르며, 회사 설정에 따라 다를 수 있습니다.
    """
    url = f"https://api{ZONE}.ecount.com/OAPI/V2/Purchase/SavePurchase?SESSION_ID={session_id}"
    
    # 금액 데이터에서 콤마 제거 및 숫자 변환
    def clean_num(val):
        if not val: return "0"
        return str(val).replace(",", "").replace("만원", "")

    # 이카운트 매입전표 입력 데이터 구조
    payload = {
        "PurchaseList": [
            {
                "LineNo": "1",
                "BulkDatas": {
                    "IO_DATE": data.get("date", ""), # 전표일자 (YYYYMMDD)
                    "CUST_CD": "00000",             # 거래처코드 (수정 필요)
                    "PROD_CD": "CAR_PURCHASE",      # 품목코드 (이카운트에 등록된 코드)
                    "QTY": "1",
                    "PRICE": clean_num(data.get("price")),
                    "SUPPLY_AMT": clean_num(data.get("price")),
                    "VAT_AMT": "0",
                    "REMARKS_1": f"{data.get('plate')} / {data.get('car_name_remit')}",
                    "REMARKS_2": data.get("vin", ""),
                    "REMARKS_3": f"딜러: {data.get('biz_name')}"
                }
            }
        ]
    }
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"네트워크 오류: {str(e)}"}
