import requests
import json
from datetime import datetime
import urllib3
import re

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# [설정] 발급받으신 정보
COM_CODE = "682186"
USER_ID = "이규성"
API_CERT_KEY = "016d41c0a7f4b4982b3032b8fddf5f2a86"
ZONE = "AD" 

def get_session_id():
    """세션 획득"""
    login_url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/OAPILogin"
    payload = {
        "COM_CODE": COM_CODE,
        "USER_ID": USER_ID,
        "API_CERT_KEY": API_CERT_KEY,
        "ZONE": ZONE 
    }
    try:
        response = requests.post(login_url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            return res_data["Data"]["Datas"]["SESSION_ID"], None
        else:
            return None, res_data
    except Exception as e:
        return None , {"Status": "500", "Message": str(e)}

def check_item_exists(session_id, prod_cd):
    """품목 존재 여부 확인"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/GetListBasicProduct?SESSION_ID={session_id}"
    payload = {"PROD_CD": str(prod_cd)}
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            items = res_data.get("Data", {}).get("Datas", [])
            return len(items) > 0, items[0] if items else None
        return False, None
    except Exception:
        return False, None

def check_customer_exists(session_id, biz_num):
    """거래처 존재 여부 확인"""
    cust_code = re.sub(r'[^0-9]', '', str(biz_num))
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/CustomerCenter/GetListCustomer?SESSION_ID={session_id}"
    payload = {"CUST": cust_code}
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        res_data = response.json()
        if str(res_data.get("Status")) == "200":
            customers = res_data.get("Data", {}).get("Datas", [])
            return len(customers) > 0
        return False
    except Exception:
        return False

def register_item(data, session_id, sheet_no):
    """신규 품목 등록"""
    url = f"https://oapi{ZONE}.ecount.com/OAPI/V2/InventoryBasic/SaveBasicProduct?SESSION_ID={session_id}"
    
    def to_float(val):
        try:
            clean = re.sub(r'[^0-9.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    l, w, h = to_float(data.get("length")), to_float(data.get("width")), to_float(data.get("height"))
    cmb_val = (l / 1000) * (w / 1000) * (h / 1000)

    payload = {
        "ProductList": [{
            "BulkDatas": {
                "PROD_CD": str(data.get("vin", "")),
                "PROD_DES": str(data.get("car_name_remit", "")),
                "UNIT": "EA",
                "ADD_TXT_01_T": str(data.get("brand", "")),
                "CONT1": str(sheet_no),
                "CONT2": str(data.get("plate", "")),
                "CONT3": str(data.get("km", "")),
                "CONT4": str(data.get("color", "")),
                "CONT5": str(data.get("year", "")),
                "ADD_DATE_01_T": datetime.now().strftime("%Y%m%d"),
                "NO_USER2": l, "NO_USER3": w, "NO_USER4": h,
                "NO_USER6": round(cmb_val, 4)
            }
        }]
    }
    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": str(e)}

def register_purchase(data, session_id, username):
    """이카운트 API 테스트 성공 데이터를 기반으로 한 구매입력"""
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={SESSION_ID}"
    
    # 1. 금액 처리 (숫자만 추출하여 문자열로 변환)
    def to_amt_str(val):
        if not val: return "0"
        clean = re.sub(r'[^0-9.]', '', str(val))
        try:
            num = float(clean)
            if "만원" in str(val):
                return str(int(num * 10000))
            return str(int(num))
        except: return "0"

    # 2. 테스트 성공했던 구조 그대로 BulkDatas 구성
    # API 테스트에서 성공한 key값들과 형식을 그대로 유지합니다.
    purchase_data = {
        "PurchasesList": [{
            "BulkDatas": {
                "IO_DATE": datetime.now().strftime("%Y%m%d"), # 오늘 날짜
                "CUST": re.sub(r'[^0-9]', '', str(data.get("biz_num", ""))), # 사업자번호
                "PROD_CD": str(data.get("vin", "")), # 차대번호
                "QTY": "1",
                "WH_CD": "100",
                "PRICE": to_amt_str(data.get("price")) # 금액
            }
        }]
    }

    try:
        # verify=False는 유지, json 파라미터로 데이터 전송
        response = requests.post(url, json=purchase_data, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신오류: {str(e)}"}

def register_purchase_test(ZONE, session_id):
    """이카운트 매뉴얼 예시와 100% 동일한 페이로드 테스트"""
    url = f"https://sboapi{ZONE}.ecount.com/OAPI/V2/Purchases/SavePurchases?SESSION_ID={SESSION_ID}"
    
    # 요청하신 예시와 완전히 동일한 구조 (값은 비어있거나 예시값 그대로)
    # 이카운트 매뉴얼 제공 예시 구조와 100% 동일
    payload = {
        "PurchasesList": [
            {
                "BulkDatas": {
                    "ORD_DATE": "", "ORD_NO": "", "IO_DATE": "20191012", "UPLOAD_SER_NO": "",
                    "CUST": "00001", "CUST_DES": "(주)OO산업", "EMP_CD": "", "WH_CD": "00001",
                    "IO_TYPE": "", "EXCHANGE_TYPE": "", "EXCHANGE_RATE": "", "SITE": "",
                    "PJT_CD": "", "DOC_NO":"", "U_MEMO1": "", "U_MEMO2": "", "U_MEMO3": "",
                    "U_MEMO4": "", "U_MEMO5": "", "U_TXT1": "", "TTL_CTT": "", "PROD_CD": "00001",
                    "PROD_DES": "test", "SIZE_DES": "", "UQTY": "", "QTY": "1", "PRICE": "",
                    "USER_PRICE_VAT": "", "SUPPLY_AMT": "", "SUPPLY_AMT_F": "", "VAT_AMT": "",
                    "REMARKS": "", "ITEM_CD": "", "P_AMT1": "", "P_AMT2": "", "P_REMARKS1": "",
                    "P_REMARKS2": "", "P_REMARKS3": "", "CUST_AMT": ""
                }
            },
            {
                "BulkDatas": {
                    "ORD_DATE": "", "ORD_NO": "", "IO_DATE": "20191012", "UPLOAD_SER_NO": "",
                    "CUST": "00001", "CUST_DES": "(주)OO산업", "EMP_CD": "", "WH_CD": "00001",
                    "IO_TYPE": "", "EXCHANGE_TYPE": "", "EXCHANGE_RATE": "", "PJT_CD": "",
                    "DOC_NO":"", "U_MEMO1": "", "U_MEMO2": "", "U_MEMO3": "", "U_MEMO4": "",
                    "U_MEMO5": "", "U_TXT1": "", "TTL_CTT": "", "PROD_CD": "00001",
                    "PROD_DES": "test", "SIZE_DES": "", "UQTY": "", "QTY": "1", "PRICE": "",
                    "USER_PRICE_VAT": "", "SUPPLY_AMT": "", "SUPPLY_AMT_F": "", "VAT_AMT": "",
                    "REMARKS": "", "ITEM_CD": "", "P_AMT1": "", "P_AMT2": "", "P_REMARKS1": "",
                    "P_REMARKS2": "", "P_REMARKS3": "", "CUST_AMT": ""
                    }
                }
            ]
        }

    try:
        response = requests.post(url, json=payload, verify=False, timeout=15)
        return response.json()
    except Exception as e:
        return {"Status": "500", "Message": f"통신 오류: {str(e)}"}
