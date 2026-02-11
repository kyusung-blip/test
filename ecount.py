import requests
import json
import urllib3

# SSL 인증서 관련 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 설정 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD"

def get_session_id():
    """검증용 SBO 서버 로그인"""
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

def verify_registration(session_id):
    """이카운트 매뉴얼 표준 샘플 데이터를 전송하여 검증 완료"""
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/SaveBasicProduct?SESSION_ID={session_id}"
    
    # 매뉴얼에서 제공된 BulkDatas 표준 샘플 구조 그대로 사용
    payload = {
        "ProductList": [
            {
                "BulkDatas": {
                    "PROD_CD": "00001",
                    "PROD_DES": "Test Product",
                    "SIZE_FLAG": "", "SIZE_DES": "", "UNIT": "", "PROD_TYPE": "",
                    "SET_FLAG": "", "BAL_FLAG": "", "WH_CD": "", "IN_PRICE": "",
                    "IN_PRICE_VAT": "", "OUT_PRICE": "", "OUT_PRICE_VAT": "",
                    "REMARKS_WIN": "", "CLASS_CD": "", "CLASS_CD2": "", "CLASS_CD3": "",
                    "BAR_CODE": "", "TAX": "", "VAT_RATE_BY": "", "CS_FLAG": "",
                    "REMARKS": "", "INSPECT_TYPE_CD": "", "INSPECT_STATUS": "",
                    "SAMPLE_PERCENT": "", "EXCH_RATE": "", "DENO_RATE": "",
                    "SAFE_A0001": "", "SAFE_A0002": "", "SAFE_A0003": "", "SAFE_A0004": "",
                    "SAFE_A0005": "", "SAFE_A0006": "", "SAFE_A0007": "", "CSORD_C0001": "",
                    "CSORD_TEXT": "", "CSORD_C0003": "", "IN_TERM": "", "MIN_QTY": "",
                    "CUST": "", "OUT_PRICE1": "", "OUT_PRICE1_VAT_YN": "", "OUT_PRICE2": "",
                    "OUT_PRICE2_VAT_YN": "", "OUT_PRICE3": "", "OUT_PRICE3_VAT_YN": "",
                    "OUT_PRICE4": "", "OUT_PRICE4_VAT_YN": "", "OUT_PRICE5": "",
                    "OUT_PRICE5_VAT_YN": "", "OUT_PRICE6": "", "OUT_PRICE6_VAT_YN": "",
                    "OUT_PRICE7": "", "OUT_PRICE7_VAT_YN": "", "OUT_PRICE8": "",
                    "OUT_PRICE8_VAT_YN": "", "OUT_PRICE9": "", "OUT_PRICE9_VAT_YN": "",
                    "OUT_PRICE10": "", "OUT_PRICE10_VAT_YN": "", "OUTSIDE_PRICE": "",
                    "OUTSIDE_PRICE_VAT": "", "LABOR_WEIGHT": "", "EXPENSES_WEIGHT": "",
                    "MATERIAL_COST": "", "EXPENSE_COST": "", "LABOR_COST": "", "OUT_COST": "",
                    "CONT1": "", "CONT2": "", "CONT3": "", "CONT4": "", "CONT5": "", "CONT6": "",
                    "NO_USER1": "", "NO_USER2": "", "NO_USER3": "", "NO_USER4": "", "NO_USER5": "",
                    "NO_USER6": "", "NO_USER7": "", "NO_USER8": "", "NO_USER9": "", "NO_USER10": "",
                    "ITEM_TYPE": "", "SERIAL_TYPE": "", "PROD_SELL_TYPE": "",
                    "PROD_WHMOVE_TYPE": "", "QC_BUY_TYPE": "", "QC_YN": ""
                }
            },
            {
                "BulkDatas": {
                    "PROD_CD": "00002",
                    "PROD_DES": "Test Product1",
                    # (중략 - 00001과 동일한 구조의 빈 필드들)
                    "PROD_WHMOVE_TYPE": "", "QC_BUY_TYPE": "", "QC_YN": ""
                }
            }
        ]
    }
    
    # 00002 데이터 채우기 (생략된 필드들을 00001과 동일하게 맞춰 전송)
    # 실제 전송 시에는 모든 필드를 명시하는 것이 안전합니다.
    for key in payload["ProductList"][0]["BulkDatas"]:
        if key not in payload["ProductList"][1]["BulkDatas"]:
            payload["ProductList"][1]["BulkDatas"][key] = ""

    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": str(e)}
